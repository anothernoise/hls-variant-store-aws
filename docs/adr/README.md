# Architecture Decision Records (ADRs)

This directory documents the significant architectural decisions made in the design and implementation of the AWS Genomic Variant Store.

## ADR Index

| ADR | Title | Status | Date |
| :--- | :--- | :---: | :---: |
| [ADR-001](ADR-001-variant-storage-strategy-selection.md) | Variant Storage Strategy Selection (S3 Tables vs Custom Iceberg vs HealthOmics vs TileDB-VCF) | **Accepted** | 2026-09-17 |
| [ADR-002](ADR-002-n-plus-1-incremental-ingestion.md) | Solving the $N+1$ Incremental Ingestion Problem via Iceberg Manifests | **Accepted** | 2026-09-17 |
| [ADR-003](ADR-003-phi-governance-and-column-level-security.md) | PHI Governance & Column-Level Security for Inherent Genomic Re-identifiability | **Accepted** | 2026-09-17 |
| [ADR-004](ADR-004-multimodal-genotype-phenotype-federation.md) | Multimodal Genotype-Phenotype Federation (OMOP CDM) without ETL | **Accepted** | 2026-09-17 |

## Status Definitions
- **Proposed**: Under review and architectural debate.
- **Accepted**: Decision approved and actively implemented in code/IaC.
- **Superseded**: Replaced by a subsequent decision record.
