-- Delta Lake: Cohort Allele Frequency
-- Aggregates allele counts and frequencies across the Delta Lake table in Amazon Athena / Databricks

SELECT reference_name, start, reference_bases, alternate_bases,
       COUNT(DISTINCT sample_id) AS total_cohort_samples,
       COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS alt_carrier_count,
       ROUND(CAST(COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS double) / 
             CAST(COUNT(DISTINCT sample_id) AS double), 4) AS carrier_frequency,
       json_extract_scalar(attributes, '$.gene') AS gene_symbol,
       json_extract_scalar(attributes, '$.clnsig') AS clinical_significance
FROM genomics_delta.variants
GROUP BY reference_name, start, reference_bases, alternate_bases,
         json_extract_scalar(attributes, '$.gene'),
         json_extract_scalar(attributes, '$.clnsig')
ORDER BY alt_carrier_count DESC
LIMIT 10;
