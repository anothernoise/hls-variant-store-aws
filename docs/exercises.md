# Lab Exercises Guide: Genomic Variant Store on AWS

This guide walks you through the five core exercises of the **Genomic Variant Store on AWS** lab.

---

## Exercise 1: Ingest Synthetic Cohort & Demonstrate N+1 Incremental Loading

### Objective
Ingest called variants from multi-sample VCF files into both **Amazon S3 Tables** and **Custom S3 + Apache Iceberg**, demonstrating that adding sample $N+1$ does not require rewriting previous cohort data.

### Step 1: Generate Deterministic Synthetic Test Data
Run the generator to create synthetic VCFs (Chr21/Chr22) and matching OMOP clinical tables:
```bash
python3 samples/generate_synthetic_data.py
```
Generated artifacts in `samples/data/`:
- `cohort_10samples.vcf`: Full 10-sample cohort.
- `cohort_batch1_samples1to5.vcf`: Baseline batch (samples 1–5).
- `cohort_batch2_samples6to10.vcf`: Incremental batch (samples 6–10).
- `person.csv` & `condition_occurrence.csv`: OMOP clinical tables.

### Step 2: Ingest into Amazon S3 Tables
Load the baseline batch, followed by the incremental batch:
```bash
# Dry run / inspection
python3 ingest/s3tables/load_variants.py --vcf samples/data/cohort_batch1_samples1to5.vcf --dry-run
python3 ingest/s3tables/load_variants.py --vcf samples/data/cohort_batch2_samples6to10.vcf --dry-run

# Live AWS load (after terraform apply)
TABLE_BUCKET=$(terraform -chdir=deploy/terraform output -raw s3tables_table_bucket_name)
python3 ingest/s3tables/load_variants.py \
    --vcf samples/data/cohort_10samples.vcf \
    --table-bucket "$TABLE_BUCKET" \
    --namespace genomics \
    --table variants
```

### Step 3: Ingest into Custom S3 + Iceberg
Load partitioned batch files into the custom warehouse directory:
```bash
python3 ingest/custom_iceberg/load_variants_custom.py \
    --vcf samples/data/cohort_batch1_samples1to5.vcf \
    --batch-id 001 \
    --dry-run

python3 ingest/custom_iceberg/load_variants_custom.py \
    --vcf samples/data/cohort_batch2_samples6to10.vcf \
    --batch-id 002 \
    --dry-run
```
Notice that Batch 2 writes new partition files (`data_batch_002.*`) without modifying `data_batch_001.*`.

---

## Exercise 2: Query Parity Across Both Stores

### Objective
Execute the three core population genomics queries on both storage tiers and verify that query results are identical.

### Query 1: Cohort Allele Frequency
Calculates Allele Count ($AC$), Allele Number ($AN$), and Allele Frequency ($AF$) with chromosome partition pruning:
- **S3 Tables**: Run [`queries/s3tables/01_allele_frequency.sql`](../queries/s3tables/01_allele_frequency.sql)
- **Custom Iceberg**: Run [`queries/custom_iceberg/01_allele_frequency.sql`](../queries/custom_iceberg/01_allele_frequency.sql)

### Query 2: Target Variant Carrier Discovery
Finds all heterozygous and homozygous alternate carriers for a clinically relevant locus (`APP chr21:25891796 A>G`):
- **S3 Tables**: Run [`queries/s3tables/02_carrier_lookup.sql`](../queries/s3tables/02_carrier_lookup.sql)
- **Custom Iceberg**: Run [`queries/custom_iceberg/02_carrier_lookup.sql`](../queries/custom_iceberg/02_carrier_lookup.sql)

### Query 3: Gene Burden Roll-up
Aggregates total alternate allele burden count and pathogenic call counts per sample for the `APP` gene:
- **S3 Tables**: Run [`queries/s3tables/03_gene_burden_rollup.sql`](../queries/s3tables/03_gene_burden_rollup.sql)
- **Custom Iceberg**: Run [`queries/custom_iceberg/03_gene_burden_rollup.sql`](../queries/custom_iceberg/03_gene_burden_rollup.sql)

---

## Exercise 3: Benchmark Query Latency, Scanned Volume, and Ingest Overhead

### Objective
Measure query execution time, data scan volumes, dollar costs in Athena, and quantify the speedup of incremental $N+1$ ingestion.

### Running the Automated Benchmark Suite
```bash
python3 benchmarks/benchmark_runner.py --cohort-size 10 --export-json benchmarks/results.json
```

### Analysis Points:
1. **Partition Pruning**: Notice that filtering by `reference_name = 'chr21'` scans only the target chromosome partition, reducing scanned volume by ~95% compared to full-cohort scans.
2. **Cost Calculation**: Athena pricing is \$5.00 per TB scanned (with a 10 MB minimum per query). At cohort size 10, each query incurs less than \$0.0001.
3. **$N+1$ Ingestion Speedup**: Incremental batch appends run $\sim 3\times$ faster on small cohorts and $>100\times$ faster on population cohorts compared to full re-ingestion.

---

## Exercise 4: Genotype ↔ OMOP CDM Clinical Join

### Objective
Directly join genomic variant carrier calls to synthetic electronic health record (EHR) phenotypes modeled in OMOP CDM without moving or duplicating data.

### Execution
Execute the cross-modal federated join queries in Athena:
- **S3 Tables**: Run [`queries/s3tables/04_omop_phenotype_join.sql`](../queries/s3tables/04_omop_phenotype_join.sql)
- **Custom Iceberg**: Run [`queries/custom_iceberg/04_omop_phenotype_join.sql`](../queries/custom_iceberg/04_omop_phenotype_join.sql)

### Expected Insight:
The query connects carriers of the pathogenic `APP chr21:25891796 A>G` mutation (`sample_002`, `sample_005`, `sample_008`) to their corresponding diagnosis in the OMOP `condition_occurrence` table: `43530807` (*Early-onset Alzheimer Disease*).

---

## Exercise 5: Governance with AWS Lake Formation & KMS

### Objective
Enforce column-level access control to treat genomic variants as high-sensitivity PHI while allowing researchers to query non-identifying locus annotations.

### Access Control Verification:
1. **Genomic Researcher Role (`analyst`)**:
   - Querying `SELECT reference_name, start, end, reference_bases, alternate_bases, attributes FROM variants` succeeds.
   - Querying `SELECT sample_id, genotype FROM variants` is **BLOCKED** or returns masked nulls via Lake Formation Column Projection Filters.
2. **Clinical Geneticist / Data Steward Role (`clinical_steward`)**:
   - Querying `SELECT * FROM variants` returns all columns, including sensitive individual calls.
3. **KMS Cryptographic Enforcement**:
   - All S3 data buckets and Athena outputs are encrypted with a Customer Managed Key (`aws_kms_key.genomics`). Access without explicit KMS key permissions is denied.
