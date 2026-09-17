-- PostgreSQL / Amazon Aurora: Pathogenic Carrier Lookup
-- Point query utilizing B-Tree index on (reference_name, start)

SELECT sample_id, reference_name, start, reference_bases, alternate_bases,
       genotype, dp, gq, allele_depth,
       attributes->>'gene' AS gene_symbol,
       attributes->>'clnsig' AS clinical_significance
FROM variants
WHERE reference_name = 'chr21' 
  AND start = 25891796 
  AND genotype IN ('0/1', '1/1');
