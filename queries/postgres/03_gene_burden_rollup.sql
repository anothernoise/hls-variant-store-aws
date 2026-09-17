-- PostgreSQL / Amazon Aurora: Gene Burden Rollup
-- Aggregates mutation burden leveraging GIN index on attributes JSONB

SELECT v.sample_id,
       v.attributes->>'gene' AS gene_symbol,
       COUNT(DISTINCT v.start) AS distinct_variant_sites,
       SUM(CASE WHEN v.genotype = '0/1' THEN 1 WHEN v.genotype = '1/1' THEN 2 ELSE 0 END) AS total_alt_allele_burden
FROM variants v
WHERE v.reference_name = 'chr21'
  AND v.genotype IN ('0/1', '1/1')
  AND v.attributes->>'gene' = 'APP'
GROUP BY v.sample_id, v.attributes->>'gene';
