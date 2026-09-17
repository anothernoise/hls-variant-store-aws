# ADR-003: PHI Governance & Column-Level Security for Inherent Genomic Re-identifiability

## Status
**Accepted** (2026-09-17)

## Context
Genomic DNA sequence and variant data present exceptional data governance and regulatory challenges under HIPAA (Safe Harbor & Expert Determination rules) and GDPR:
1. **Quasi-Identifiers & Re-identification**: Unlike tabular medical billing data, an individual's genome is inherently identifying. Independent studies have demonstrated that as few as 30–75 rare single nucleotide variants (SNVs) can uniquely identify a patient when cross-referenced against genealogy databases or public research callsets.
2. **Dual-Use Data Dilemma**:
   - **Locus-Level Annotations** (`reference_name`, `start`, `end`, `ref`, `alt`, `gene_symbol`, `clinical_significance`, cohort allele frequency) represent non-identifying aggregate scientific facts.
   - **Sample Genotype Matrices** (`sample_id`, `genotype`, `dp`, `gq`, `allele_depth`) directly tie genetic calls to individual clinical study subjects.

Giving broad research teams unrestricted access to the complete variant table violates the Principle of Least Privilege and creates catastrophic compliance risk.

## Decision
Implement a **dual-persona, column-level access control model using AWS Lake Formation and AWS KMS**:
1. **KMS Customer Managed Key (SSE-KMS)**:
   - All S3 Table Buckets, custom warehouse buckets, and Athena query result locations are encrypted with a dedicated Customer Managed Key (`aws_kms_key.genomics`).
   - S3 Tables maintenance principals (`tables.s3.amazonaws.com`) and Athena query engines must authenticate against specific key policy conditions.
2. **Lake Formation Column-Level Security (CLS)**:
   - **Genomic Researcher Role (`analyst`)**: Granted `SELECT` permission strictly on locus-level and cohort-level columns (`reference_name`, `start`, `end`, `ref`, `alt`, `qual`, `filter`, `dp`, `gq`, `attributes`, `cohort_id`). Sensitive PHI columns (`sample_id`, `genotype`, `allele_depth`) are blocked/masked at the query engine layer.
   - **Clinical Geneticist / Data Steward Role (`clinical_steward`)**: Granted full wildcard column access across all attributes for clinical diagnosis and direct phenotype correlation.
3. **Audit Trails**:
   - CloudTrail S3 Data Events log every storage request.
   - Lake Formation and Athena audit logs track user identity, query execution, and column projections.

## Consequences
- Protects patient privacy without duplicating datasets into "public" and "private" copies.
- Ensures compliance with HIPAA Safe Harbor de-identification standards for bioinformatics researchers.
- Requires deploying principals in AWS to maintain Lake Formation administrative privileges.
