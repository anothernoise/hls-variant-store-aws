-- Query 04: Cross-Modal Join: Custom S3 Iceberg Variants ↔ OMOP CDM Phenotype
-- Strategy: S3 + Apache Iceberg (Custom/DIY)
-- Engine: Amazon Athena (Presto/Trino SQL)
-- Databases: genomics_custom_iceberg (variants) & clinical_omop (person, condition_occurrence)
--
-- Objective:
-- Evaluate clinical condition occurrences (phenotypes) among carriers of target
-- pathogenic variants versus non-carriers in the synthetic cohort.

WITH target_carriers AS (
    SELECT
        v.sample_id,
        v.reference_name,
        v.start,
        v.genotype,
        json_extract_scalar(v.attributes, '$.gene') AS gene_symbol,
        json_extract_scalar(v.attributes, '$.clnsig') AS clinical_significance
    FROM
        genomics_custom_iceberg.variants v
    WHERE
        v.reference_name = 'chr21'
        AND v.start = 25891796 -- APP Pathogenic SNV
        AND v.genotype IN ('0/1', '1/1')
)
SELECT
    p.person_id,
    p.sample_id,
    p.year_of_birth,
    CASE p.gender_concept_id
        WHEN 8507 THEN 'MALE'
        WHEN 8532 THEN 'FEMALE'
        ELSE 'UNKNOWN'
    END AS gender,
    tc.gene_symbol,
    tc.clinical_significance,
    tc.genotype,
    co.condition_concept_id,
    co.condition_start_date,
    CASE
        WHEN co.condition_concept_id = 43530807 THEN 'Early-onset Alzheimer Disease (Confirmed)'
        ELSE 'Other Clinical Condition'
    END AS phenotype_label
FROM
    clinical_omop.person p
INNER JOIN
    target_carriers tc ON p.sample_id = tc.sample_id
LEFT JOIN
    clinical_omop.condition_occurrence co ON p.person_id = co.person_id
ORDER BY
    p.person_id ASC;
