# ADR-001: Variant Storage Strategy Selection

## Status
**Accepted** (2026-09-17)

## Context
A population-scale genomic variant store must support:
1. High-throughput ingestion of multi-sample called variants (VCF/gVCF).
2. Low-cost, interactive cohort SQL queries (allele frequencies, carrier lookups, gene burden).
3. Zero-downtime incremental sample additions ($N+1$ problem).
4. Direct joinability to clinical phenotype data (OMOP CDM).
5. Strict HIPAA/GDPR PHI compliance.

We evaluated four candidate architectural strategies on AWS:
- **AWS HealthOmics Variant Store**: Fully managed AWS service with built-in genomics parsers and Lake Formation integration.
- **Amazon S3 Tables**: Managed Apache Iceberg storage tier in S3 with automated compaction, snapshot expiration, and unreferenced file removal.
- **Custom S3 + Apache Iceberg (DIY)**: Self-managed S3 bucket, Glue Catalog Iceberg table, and custom compaction routines.
- **TileDB-VCF**: Columnar sparse-array engine optimized for multi-dimensional genomic coordinates.

## Decision
1. **Primary Strategy for Managed SQL**: Adopt **Amazon S3 Tables**.
   - Provides native Apache Iceberg open table format without the operational burden of managing file compaction, manifest restructuring, or orphan file cleanup.
   - Natively federated into AWS Glue Data Catalog via `s3tablescatalog`, enabling direct SQL queries from Amazon Athena and Amazon EMR/Spark.
2. **Co-primary for Multi-Cloud / Custom Portability**: Maintain **Custom S3 + Apache Iceberg (DIY)**.
   - Provides granular control over partition layouts (`reference_name`), custom Parquet compression codecs (ZSTD/Snappy), and multi-engine portability across Athena, Trino, and Apache Spark on Kubernetes.

## Consequences

### Positive
- **Standardized Iceberg Interface**: Both S3 Tables and Custom S3 Iceberg expose an open, vendor-neutral Iceberg table format, preventing lock-in.
- **Reduced Operational Overhead**: S3 Tables eliminates the need for scheduled Glue compaction jobs or Airflow maintenance DAGs.
- **Cost Efficiency**: Serverless Athena queries scan only relevant columnar Parquet blocks and pruned partitions, keeping query costs minimal (\$5.00/TB scanned).

### Negative / Trade-offs
- S3 Tables is an AWS-specific storage tier; while the underlying table is open Apache Iceberg, table bucket APIs are specific to AWS.
- Custom S3 Iceberg requires the engineering team to monitor small-file fragmentation if high-frequency incremental appends are executed without regular compaction.
