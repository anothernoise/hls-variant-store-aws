-- Query 03: Gene-Level Variant Burden Rollup
-- Engine: Amazon Athena (Presto/Trino SQL)
-- Storage: Amazon S3 Tables (Apache Iceberg)
--
-- Features:
-- - Aggregates high-impact/pathogenic variant count per sample for a target gene
-- - Demonstrates population cohort burden testing logic

SELECT
    v.sample_id,
    json_extract_scalar(v.attributes, '$.gene') AS gene_symbol,
    COUNT(DISTINCT v.start) AS distinct_variant_sites,
    SUM(
        CASE
            WHEN v.genotype = '0/1' THEN 1
            WHEN v.genotype = '1/1' THEN 2
            ELSE 0
        END
    ) AS total_alt_allele_burden,
    COUNT(
        CASE
            WHEN json_extract_scalar(v.attributes, '$.clnsig') = 'PATHOGENIC' THEN 1
        END
    ) AS pathogenic_variant_count
FROM
    s3tablescatalog.genomics.variants v
WHERE
    v.reference_name = 'chr21'
    AND v.genotype IN ('0/1', '1/1')
    AND json_extract_scalar(v.attributes, '$.gene') = 'APP'
GROUP BY
    v.sample_id,
    json_extract_scalar(v.attributes, '$.gene')
ORDER BY
    total_alt_allele_burden DESC,
    v.sample_id ASC;
