# Genomic Variant Store Benchmark Methodology

This benchmark suite evaluates the trade-offs across storage strategies for population-scale genomic variant storage on AWS.

## Metrics Evaluated

### 1. Query Latency & Pruning Efficiency
- **Chromosome Partition Pruning**: Evaluates query latency when queries include `WHERE reference_name = 'chr21'`. Non-target chromosome partitions (e.g., `chr22`, `chr1`..`chr20`) are pruned at the metadata layer before reading Parquet footers.
- **Column Pruning**: Queries filtering on locus attributes (`start`, `ref`, `alt`) scan only metadata and positional columns without loading genotype payloads (`dp`, `gq`, `allele_depth`).

### 2. Query Scanned Volume & Cost Formula
Amazon Athena charges \$5.00 per terabyte (TB) of data scanned, with a 10 MB minimum per query.

$$\text{Billable Bytes} = \max(\text{Bytes Scanned}, 10 \times 1024^2)$$

$$\text{Query Cost (USD)} = \frac{\text{Billable Bytes}}{1024^4} \times 5.00$$

### 3. The $N+1$ Incremental Ingestion Problem
In traditional genomic pipelines, adding a single new patient sample (sample $N+1$) often triggers a complete joint-calling or cohort re-aggregation step across all previous $N$ samples ($O(N)$ write amplification).

#### Comparison:
- **Naive Full Recompute**: Rewrites all previously stored sample records plus the new sample into rewritten partition files.
- **Iceberg / S3 Tables Incremental Append**: Commits new Parquet files containing only sample $N+1$ into the existing partition structure (`reference_name=chr.../data_batch_*.parquet`). The Iceberg manifest list records the snapshot change in milliseconds ($O(1)$ write amplification).

---

## Running Benchmarks Locally & on AWS

### Local Simulation Mode
```bash
python3 benchmarks/benchmark_runner.py --cohort-size 10 --export-json benchmarks/results.json
```

### Athena Live Benchmark Mode
Deploy infrastructure via Terraform and run the queries in `queries/s3tables/` and `queries/custom_iceberg/` in the Athena Console or via AWS CLI to capture live CloudWatch metrics:
- `QueryExecutionId`
- `EngineExecutionTimeInMillis`
- `DataScannedInBytes`
