# ADR-004: Multimodal Genotype-Phenotype Federation (OMOP CDM) without ETL

## Status
**Accepted** (2026-09-17)

## Context
Precision medicine and clinical genomics research require correlating genetic variation (genotype) with electronic health record (EHR) phenotypes, such as disease diagnoses, lab test measurements, and medication responses.
The international standard for clinical observational research is the **OMOP Common Data Model (CDM)** (OHDSI consortium).

Traditionally, uniting genomic data with clinical records required heavy, fragile ETL pipelines that:
1. Exported variant calls out of genomic databases into relational databases, or
2. Enriched EHR databases with massive variant tables, creating storage bloat and sync delays.

## Decision
Adopt **Zero-ETL Query Federation across S3 Tables and OMOP Glue Catalogs using Amazon Athena / Trino**:
1. **Clinical Layer**: Store OMOP CDM tables (`person`, `condition_occurrence`, `measurement`, `drug_exposure`) in standard columnar/CSV format registered in the AWS Glue Data Catalog (`clinical_omop`).
2. **Genomic Layer**: Store called variants in Apache Iceberg format managed by Amazon S3 Tables (`s3tablescatalog.genomics.variants`) or Custom S3 Iceberg (`genomics_custom_iceberg.variants`).
3. **Cross-Modal SQL Federation**: Query engines (Athena Presto/Trino) perform in-place distributed joins directly between `s3tablescatalog` and `clinical_omop` using standard SQL:
   ```sql
   SELECT
       p.person_id,
       tc.gene_symbol,
       co.condition_concept_id,
       co.condition_start_date
   FROM
       clinical_omop.person p
   INNER JOIN
       target_carriers tc ON p.sample_id = tc.sample_id
   LEFT JOIN
       clinical_omop.condition_occurrence co ON p.person_id = co.person_id
   ```

## Consequences
- **Zero Data Duplication**: Neither the genomic store nor the EHR warehouse duplicates records.
- **Dynamic Exploration**: Clinicians can change variant filters (e.g. pathogenic vs VUS) and condition ICD/SNOMED concept IDs interactively without rebuilding data pipelines.
- **Cost Minimization**: Only the matched carrier sample records and clinical rows are materialized during query execution.
