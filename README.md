# hls-variant-store-aws

> Companion **starter** lab for the [Health & Life Science Solution Bootcamp](https://github.com/anothernoise/hls-sa).
> The full reference solution lives in the private `hls-bootcamp-solutions` repo.

Design, build, and **benchmark** a population-scale **genomic variant store on AWS** across
four implementation strategies — then join it to clinical (OMOP) data. The lab teaches the
trade-offs an SA weighs when storing and querying variants at scale.

## What you build

```mermaid
flowchart LR
  VCF["gVCF / VCF (synthetic)"] --> Ingest["Ingest + convert"]
  Ingest --> S3T["S3 Tables (managed Iceberg)"]
  Ingest --> Ice["S3 + Iceberg (custom)"]
  Ingest --> HO["HealthOmics variant store"]
  Ingest --> TDB["TileDB-VCF"]
  S3T & Ice & HO --> LF["Lake Formation (CLS + KMS)"]
  LF --> Athena["Athena / Presto SQL"]
  Athena --> Bench["Benchmark: allele freq, carriers, N+1 ingest"]
  Athena --> Join["Join to synthetic OMOP"]
```

## The Four Strategies

| Strategy | Managed? | Engine | What you learn |
| :--- | :--- | :--- | :--- |
| **S3 Tables** | Managed Iceberg | Athena / Spark | Open Iceberg format without table ops or manual compaction |
| **S3 + Iceberg (custom)** | DIY | Athena / Spark / Trino | Partitioning (`reference_name`), file sizing, schema evolution, manifest commits |
| **HealthOmics variant store** | Fully managed | Athena / Lake Formation | Managed genomics with native AWS provenance |
| **TileDB-VCF** | Self-run | TileDB API / Spark | Sparse-array variant storage for dense cohort queries |

## The Exercises

Full step-by-step instructions are available in the **[Lab Exercises Guide](docs/exercises.md)**:

1. **Ingest**: Load synthetic gVCF cohorts into Amazon S3 Tables and Custom S3 Iceberg.
2. **Query**: Run identical SQL queries across both engines (allele frequency, carrier lookup, gene burden).
3. **Benchmark**: Measure latency, data scanned, Athena costs, and the $N+1$ incremental ingest speedup.
4. **Join**: Correlate genomic variant carriers to synthetic [OMOP](https://github.com/anothernoise/hls-sa) clinical conditions without data movement.
5. **Govern**: Enforce AWS Lake Formation column projection filters and KMS Customer Managed Keys.

## Architecture Decision Records (ADRs)

All core technical decisions and trade-offs are documented in [`docs/adr/`](docs/adr/):
- [ADR-001: Storage Strategy Selection](docs/adr/ADR-001-variant-storage-strategy-selection.md)
- [ADR-002: Solving the N+1 Incremental Ingestion Problem](docs/adr/ADR-002-n-plus-1-incremental-ingestion.md)
- [ADR-003: PHI Governance & Column-Level Security](docs/adr/ADR-003-phi-governance-and-column-level-security.md)
- [ADR-004: Multimodal Genotype-Phenotype Federation (OMOP CDM)](docs/adr/ADR-004-multimodal-genotype-phenotype-federation.md)

## Repo Layout

```
.
├── deploy/terraform/         # Terraform IaC (S3 Tables, Custom Iceberg, Athena, OMOP, KMS, Lake Formation)
├── docs/
│   ├── architecture.md       # Solution design, trade-offs, and NFRs
│   ├── summary.md            # SA evaluation matrix, access patterns, Well-Architected pillars
│   ├── exercises.md          # Step-by-step lab exercise guide
│   └── adr/                  # Architecture Decision Records (ADR-001 through ADR-004)
├── samples/
│   ├── generate_synthetic_data.py # Deterministic multi-sample gVCF & OMOP generator
│   └── data/                 # Generated synthetic VCF and OMOP CSV datasets
├── ingest/
│   ├── s3tables/             # Ingestion loader for Amazon S3 Tables
│   └── custom_iceberg/       # Partition-aware loader for Custom S3 + Iceberg
├── queries/
│   ├── s3tables/             # Athena Presto/Trino SQL queries for S3 Tables
│   └── custom_iceberg/       # Athena Presto/Trino SQL queries for Custom Iceberg
├── benchmarks/
│   ├── benchmark_runner.py   # Latency, scan volume, cost & N+1 speedup benchmark harness
│   └── README.md             # Benchmark methodology and formulas
├── governance/
│   └── lakeformation_policy.md # Threat model and column access control matrix
└── tests/                    # Unit test suite for loaders and benchmark calculations
```

## Quick Start & Verification

### 1. Generate Synthetic Data
```bash
python3 samples/generate_synthetic_data.py
```

### 2. Run Unit Tests
```bash
python3 -m unittest discover tests
```

### 3. Run Benchmarks
```bash
python3 benchmarks/benchmark_runner.py --cohort-size 10
```

### 4. Deploy Infrastructure (AWS)
```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

> **Synthetic data only — genomic data is inherently identifying; never commit real data.**

## License

Proprietary — part of the Health & Life Science Solution Bootcamp. See the
[bootcamp license](https://github.com/anothernoise/hls-sa/blob/main/LICENSE); ask before reuse.
