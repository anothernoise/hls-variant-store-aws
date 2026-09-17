-- Query 04: Cross-Modal Join: S3 Tables Genomic Variants ↔ OMOP CDM Phenotype
-- Engine: Amazon Athena (Presto/Trino SQL)
--
-- Objective:
-- Evaluate clinical condition occurrences (phenotypes) among carriers of target
-- pathogenic variants versus non-carriers in the synthetic cohort.

-- Optional DDL if staging synthetic OMOP data via Athena Glue external table:
/*
CREATE EXTERNAL TABLE IF NOT EXISTS default.omop_person (
    person_id BIGINT,
    gender_concept_id INT,
    year_of_birth INT,
    month_of_birth INT,
    day_of_birth INT,
    race_concept_id INT,
    ethnicity_concept_id INT,
    sample_id STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://<results-bucket>/omop/person/'
TBLPROPERTIES ('skip.header.line.count'='1');

CREATE EXTERNAL TABLE IF NOT EXISTS default.omop_condition_occurrence (
    condition_occurrence_id BIGINT,
    person_id BIGINT,
    condition_concept_id INT,
    condition_start_date STRING,
    condition_type_concept_id INT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://<results-bucket>/omop/condition_occurrence/'
TBLPROPERTIES ('skip.header.line.count'='1');
*/

WITH target_carriers AS (
    SELECT
        v.sample_id,
        v.reference_name,
        v.start,
        v.genotype,
        json_extract_scalar(v.attributes, '$.gene') AS gene_symbol,
        json_extract_scalar(v.attributes, '$.clnsig') AS clinical_significance
    FROM
        s3tablescatalog.genomics.variants v
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
    default.omop_person p
INNER JOIN
    target_carriers tc ON p.sample_id = tc.sample_id
LEFT JOIN
    default.omop_condition_occurrence co ON p.person_id = co.person_id
ORDER BY
    p.person_id ASC;
