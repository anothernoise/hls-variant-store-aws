# hls-variant-store-aws

> Companion **starter** lab for the [Health & Life Science Solution Bootcamp](https://github.com/anothernoise/hls-sa).
> The full reference solution lives in the private `hls-bootcamp-solutions` repo.

Design, build, and **benchmark** a population-scale **genomic variant store on AWS** across
four implementation strategies — then join it to clinical (OMOP) data. The lab teaches the
trade-offs an SA weighs when storing and querying variants at scale.

## What you build

```mermaid
flowchart TB
  subgraph Presentation ["1. Presentation Layer (Port 8050)"]
    Dash["Plotly Dash Visual Explorer (app/app.py)"]
    Switch["Online / Offline Switcher"]
    Dash --- Switch
  end

  subgraph API ["2. FastAPI Middle Layer (Port 8000)"]
    FastAPI["FastAPI Application (api/main.py)"]
    Swagger["OpenAPI Swagger UI (/docs)"]
    FastAPI --- Swagger
  end

  subgraph Engines ["3. Storage Engines & Lakehouse Tier"]
    S3T["Amazon S3 Tables (Managed Iceberg)"]
    Ice["Custom S3 + Iceberg"]
    Delta["Delta Lake on S3"]
    Hail["Hail VDS (Spark)"]
    Aurora["Aurora PostgreSQL (Serverless v2)"]
    RDS["Amazon RDS PostgreSQL"]
    HO["AWS HealthOmics Variant Store"]
    OMOP["OMOP CDM v5.4 Clinical Data"]
  end

  Dash -->|"REST API / HTTP"| FastAPI
  FastAPI --> S3T & Ice & Delta & Hail & Aurora & RDS & HO
  S3T & Ice & Delta & Hail & HO -->|"In-place Federated JOIN"| OMOP
```

## Architecture Strategies Compared

| Strategy | Architecture Model | Primary Engine | Key Trade-off / Learning |
| :--- | :--- | :--- | :--- |
| **S3 Tables** | Managed Iceberg Lakehouse | Athena / Spark | Zero-ops compaction, automated table bucket maintenance |
| **S3 + Iceberg (custom)** | Self-Managed Lakehouse | Athena / Spark / Trino | Open Iceberg format, custom partition transforms (`reference_name`) |
| **Delta Lake on S3** | Databricks / ACID Lakehouse | Athena / Spark / Databricks | Parquet + `_delta_log` commits, Liquid Clustering skipping |
| **Hail VDS on S3** | Distributed Sparse MatrixTable | Apache Spark / Hail | Split Variant/Reference matrix optimized for GWAS and statistical genetics |
| **Aurora PostgreSQL** | Relational Serverless v2 | PostgreSQL 16 (JSONB) | Sub-10ms indexed point lookups, auto-scaling 0.5–2 ACUs, instant OLTP joins |
| **RDS PostgreSQL** | Relational Provisioned Instance | PostgreSQL 16 (JSONB) | Low-cost steady baseline for dev metadata and targeted carrier lookups |
| **HealthOmics** | Fully Managed Genomics Store | Athena / Lake Formation | Fully managed AWS genomics engine with provenance tracking |


## The Exercises

Full step-by-step instructions are available in the **[Lab Exercises Guide](docs/exercises.md)**:

1. **Ingest**: Load synthetic gVCF cohorts into Amazon S3 Tables and Custom S3 Iceberg.
2. **Query**: Run identical SQL queries across both engines (allele frequency, carrier lookup, gene burden).
3. **Benchmark**: Measure latency, data scanned, Athena costs, and the $N+1$ incremental ingest speedup.
4. **Join**: Correlate genomic variant carriers to synthetic [OMOP](https://github.com/anothernoise/hls-sa) clinical conditions without data movement.
5. **Govern**: Enforce AWS Lake Formation column projection filters and KMS Customer Managed Keys.
6. **Explore & Visualize**: Interactive multi-engine exploration web app (`app/app.py`) with Plotly Dash and FastAPI middle layer (`api/main.py`), supporting dynamic backend switching across 7 storage architectures.

## Architecture Decision Records (ADRs)

All core technical decisions and trade-offs are documented in [`docs/adr/`](docs/adr/):
- [ADR-001: Storage Strategy Selection](docs/adr/ADR-001-variant-storage-strategy-selection.md)
- [ADR-002: Solving the N+1 Incremental Ingestion Problem](docs/adr/ADR-002-n-plus-1-incremental-ingestion.md)
- [ADR-003: PHI Governance & Column-Level Security](docs/adr/ADR-003-phi-governance-and-column-level-security.md)
- [ADR-004: Multimodal Genotype-Phenotype Federation (OMOP CDM)](docs/adr/ADR-004-multimodal-genotype-phenotype-federation.md)

## Solution Architect Case Studies & Decision Framework

Real-world customer scenarios and architectural decision rubrics are documented in **[`docs/sa_case_studies.md`](docs/sa_case_studies.md)**:
- **Case Study 1 (Fully Solved Example)**: National Genomic Medicine Service (50K WGS) — Dual-Tier Lakehouse (S3 Tables + Aurora Serverless v2).
- **Case Study 2 (SA Challenge Task A)**: Global Population Genetics Consortium (500K WGS) — Ephemeral Hail VDS on EMR Spot.
- **Case Study 3 (SA Challenge Task B)**: Global Precision Oncology Platform (30K Patients) — Delta Lake on S3 with Delta Sharing.

## Repo Layout

```
.
├── api/                      # FastAPI middle layer service (Port 8000)
│   ├── main.py               # Application entry point, CORS, OpenAPI Swagger docs
│   ├── schemas.py            # Pydantic validation schemas (telemetry, query, engines)
│   └── routers/              # Modular REST routers (engines.py, benchmarks.py)
├── app/                      # Interactive Plotly Dash multi-engine explorer web app (Port 8050)
│   ├── app.py                # Dash UI layout, switcher, and discovery callbacks
│   ├── api_client.py         # HTTP client connecting Dash UI to FastAPI middle layer
│   ├── backend.py            # Dynamic per-engine SQL execution & Athena data access layer
│   ├── metadata/             # Engine JSON configuration files (7 storage architectures)
│   │   ├── loader.py         # Dynamic metadata loader
│   │   └── *.json            # Schema & architecture profiles per engine
│   └── requirements.txt      # Web app and API Python dependencies
├── deploy/terraform/         # Terraform IaC (S3 Tables, Iceberg, Athena, RDS, Aurora, HealthOmics, KMS)
├── docs/
│   ├── architecture.md       # 3-tier architecture, trade-offs, and NFRs
│   ├── summary.md            # SA evaluation matrix, decision tree, Well-Architected pillars
│   ├── exercises.md          # Step-by-step lab exercise guide (Exercises 1 through 6)
│   ├── sa_case_studies.md    # Real-world SA case studies (1 solved, 2 challenge tasks)
│   └── adr/                  # Architecture Decision Records (ADR-001 through ADR-004)
├── samples/
│   ├── generate_synthetic_data.py # Deterministic multi-sample gVCF & OMOP generator
│   └── data/                 # Generated synthetic VCF and OMOP CSV datasets
├── ingest/
│   ├── s3tables/             # Ingestion loader for Amazon S3 Tables
│   ├── custom_iceberg/       # Partition-aware loader for Custom S3 + Iceberg
│   └── healthomics/          # Lifecycle & async VCF import manager for AWS HealthOmics
├── queries/
│   ├── s3tables/             # Athena SQL queries for S3 Tables
│   ├── custom_iceberg/       # Athena SQL queries for Custom Iceberg
│   ├── delta/                # Athena SQL queries for Delta Lake
│   └── postgres/             # PostgreSQL JSONB queries for Aurora / RDS
├── scripts/
│   ├── manage_infra.py       # Engine-selective deployment, destruction & status CLI
│   └── validate_exercises.py # Automated validation CLI (local-mode and live aws-mode)
├── benchmarks/
│   ├── benchmark_runner.py   # Latency, scan volume, cost & N+1 speedup benchmark harness
│   └── live_performance_report.md # Empirical Athena execution & cost telemetry
├── governance/
│   └── lakeformation_policy.md # Threat model and column access control matrix
└── tests/                    # TDD unit test suite (54 tests passing)
```

## Quick Start & Verification

### 1. Install Dependencies
```bash
pip install -r app/requirements.txt
```

### 2. Generate Synthetic Data
```bash
python3 samples/generate_synthetic_data.py
```

### 3. Launch FastAPI Middle Layer Service (Port 8000)
```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
# OpenAPI Swagger Documentation: http://localhost:8000/docs
# Interactive ReDoc: http://localhost:8000/redoc
```

### 4. Launch Interactive Dash Visualization UI (Port 8050)
```bash
python3 app/app.py
# Open http://localhost:8050 to explore the cohort and switch between all 7 engines
```

### 5. Run Full Unit Test Suite (TDD)
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### 6. Inspect Live Infrastructure Status
```bash
python3 scripts/manage_infra.py --action status --profile default
```

> **Synthetic data only — genomic data is inherently identifying; never commit real data.**

## License

Proprietary — part of the Health & Life Science Solution Bootcamp. See the
[bootcamp license](https://github.com/anothernoise/hls-sa/blob/main/LICENSE); ask before reuse.
