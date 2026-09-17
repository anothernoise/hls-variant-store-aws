-- Delta Lake: Gene Burden Rollup
-- Aggregates alternate allele burden per sample for the APP gene

SELECT v.sample_id,
       json_extract_scalar(v.attributes, '$.gene') AS gene_symbol,
       COUNT(DISTINCT v.start) AS distinct_variant_sites,
       SUM(CASE WHEN v.genotype = '0/1' THEN 1 WHEN v.genotype = '1/1' THEN 2 ELSE 0 END) AS total_alt_allele_burden
FROM genomics_delta.variants v
WHERE v.reference_name = 'chr21'
  AND v.genotype IN ('0/1', '1/1')
  AND json_extract_scalar(v.attributes, '$.gene') = 'APP'
GROUP BY v.sample_id, json_extract_scalar(v.attributes, '$.gene');
