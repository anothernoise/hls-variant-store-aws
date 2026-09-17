# Governance & PHI Protection: AWS Lake Formation Controls

## 1. Threat Model & Regulatory Requirements (HIPAA / GDPR)

Genomic sequence and called variant data possess unique privacy characteristics:
1. **Inherent Re-identifiability**: A small panel of 30–75 independent single-nucleotide variants (SNVs) can uniquely identify an individual human being across public or commercial reference databases.
2. **High-Sensitivity PHI**: Because variants cannot be truly anonymized or de-identified once linked to individual sample IDs, variant call sets with sample linkage must be governed as high-sensitivity Protected Health Information (PHI).
3. **Data Segregation Mandate**: Population frequency statistics (e.g., $AF$, $AC$, $AN$, gene symbols) are aggregate scientific knowledge and can be safely shared with broad research teams. In contrast, individual genotype matrices (`sample_id`, `genotype`, `dp`, `gq`, `allele_depth`) must remain strictly isolated to authorized clinical geneticists and data stewards.

---

## 2. Column-Level Access Control Matrix

AWS Lake Formation enforces fine-grained column projection filters at the Athena engine layer:

| Column Name | Classification | Genomic Researcher Role | Clinical Steward Role |
| :--- | :--- | :---: | :---: |
| `reference_name` | Public / De-identified | **Allowed** | **Allowed** |
| `start` | Public / De-identified | **Allowed** | **Allowed** |
| `end` | Public / De-identified | **Allowed** | **Allowed** |
| `reference_bases` | Public / De-identified | **Allowed** | **Allowed** |
| `alternate_bases` | Public / De-identified | **Allowed** | **Allowed** |
| `qual` | Public / De-identified | **Allowed** | **Allowed** |
| `filter` | Public / De-identified | **Allowed** | **Allowed** |
| `dp` | Locus Metric | **Allowed** | **Allowed** |
| `gq` | Locus Metric | **Allowed** | **Allowed** |
| `attributes` (Gene, ClnSig) | Public Annotation | **Allowed** | **Allowed** |
| `cohort_id` | Metadata | **Allowed** | **Allowed** |
| `sample_id` | **High-Sensitivity PHI** | **MASKED / BLOCKED** | **Allowed** |
| `genotype` | **High-Sensitivity PHI** | **MASKED / BLOCKED** | **Allowed** |
| `allele_depth` | **High-Sensitivity PHI** | **MASKED / BLOCKED** | **Allowed** |

---

## 3. Cryptographic Controls & Auditing

1. **Envelope Encryption with Customer Managed Key (SSE-KMS)**:
   - All S3 Table Buckets, Custom S3 Iceberg Warehouses, and Athena query result locations are encrypted with a dedicated KMS CMK (`aws_kms_key.genomics`).
   - S3 Tables maintenance principals (`tables.s3.amazonaws.com`) and Athena query execution engines require explicit KMS decryption grants.
2. **Audit Trails**:
   - **AWS CloudTrail S3 Data Events**: Captures every `GetObject` and `PutObject` invocation against warehouse buckets.
   - **Lake Formation Audit Logging**: Logs every table and column-level authorization check.
   - **Athena Query History**: Persists SQL execution history, user identities, and bytes scanned metrics.
