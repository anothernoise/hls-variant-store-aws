-- Delta Lake: Pathogenic Carrier Lookup
-- Point query for Alzheimer's pathogenic mutation APP chr21:25891796 A>G

SELECT sample_id, reference_name, start, reference_bases, alternate_bases,
       genotype, dp, gq, allele_depth,
       json_extract_scalar(attributes, '$.gene') AS gene_symbol,
       json_extract_scalar(attributes, '$.clnsig') AS clinical_significance
FROM genomics_delta.variants
WHERE reference_name = 'chr21' 
  AND start = 25891796 
  AND genotype IN ('0/1', '1/1');
