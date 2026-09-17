-- Query 02: Target Variant Carrier Lookup
-- Strategy: S3 + Apache Iceberg (Custom/DIY)
-- Engine: Amazon Athena (Presto/Trino SQL)
-- Database: genomics_custom_iceberg.variants
--
-- Features:
-- - Point lookup with partition pruning on `reference_name` and coordinate range
-- - Filters for carriers (heterozygous '0/1' and homozygous alternate '1/1')

SELECT
    sample_id,
    reference_name,
    start,
    reference_bases,
    alternate_bases,
    genotype,
    CASE
        WHEN genotype = '0/1' THEN 'HET'
        WHEN genotype = '1/1' THEN 'HOM_ALT'
        ELSE 'OTHER'
    END AS zygosity,
    dp AS read_depth,
    gq AS genotype_quality,
    allele_depth,
    json_extract_scalar(attributes, '$.gene') AS gene_symbol,
    json_extract_scalar(attributes, '$.clnsig') AS clinical_significance
FROM
    genomics_custom_iceberg.variants
WHERE
    reference_name = 'chr21'
    AND start = 25891796
    AND genotype IN ('0/1', '1/1')
ORDER BY
    sample_id ASC;
