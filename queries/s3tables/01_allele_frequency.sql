-- Query 01: Cohort Allele Frequency Calculation
-- Engine: Amazon Athena (Presto/Trino SQL)
-- Storage: Amazon S3 Tables (Apache Iceberg)
--
-- Features:
-- - Prunes by partition column `reference_name`
-- - Calculates Allele Count (AC), Allele Number (AN), and Allele Frequency (AF)

SELECT
    reference_name,
    start,
    end,
    reference_bases,
    alternate_bases,
    json_extract_scalar(attributes, '$.gene') AS gene_symbol,
    json_extract_scalar(attributes, '$.clnsig') AS clinical_significance,
    COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS carrier_sample_count,
    SUM(
        CASE
            WHEN genotype = '0/1' THEN 1
            WHEN genotype = '1/1' THEN 2
            ELSE 0
        END
    ) AS allele_count,
    COUNT(CASE WHEN genotype IN ('0/0', '0/1', '1/1') THEN 1 END) * 2 AS allele_number,
    ROUND(
        CAST(SUM(CASE WHEN genotype = '0/1' THEN 1 WHEN genotype = '1/1' THEN 2 ELSE 0 END) AS DOUBLE) /
        NULLIF(COUNT(CASE WHEN genotype IN ('0/0', '0/1', '1/1') THEN 1 END) * 2, 0),
        4
    ) AS cohort_allele_frequency
FROM
    s3tablescatalog.genomics.variants
WHERE
    reference_name = 'chr21'
    AND filter = 'PASS'
GROUP BY
    reference_name,
    start,
    end,
    reference_bases,
    alternate_bases,
    json_extract_scalar(attributes, '$.gene'),
    json_extract_scalar(attributes, '$.clnsig')
ORDER BY
    start ASC;
