-- PostgreSQL / Amazon Aurora: Cohort Allele Frequency
-- Aggregates variant calls using native PostgreSQL JSONB and window/aggregate functions

SELECT reference_name, start, reference_bases, alternate_bases,
       COUNT(DISTINCT sample_id) AS total_cohort_samples,
       COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS alt_carrier_count,
       ROUND(CAST(COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS numeric) / 
             CAST(COUNT(DISTINCT sample_id) AS numeric), 4) AS carrier_frequency,
       attributes->>'gene' AS gene_symbol,
       attributes->>'clnsig' AS clinical_significance
FROM variants
GROUP BY reference_name, start, reference_bases, alternate_bases,
         attributes->>'gene', attributes->>'clnsig'
ORDER BY alt_carrier_count DESC
LIMIT 10;
