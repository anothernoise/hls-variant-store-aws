-- Delta Lake: Cross-Modal OMOP Phenotype Join
-- Direct distributed SQL join between Delta Lake variants and OMOP CDM clinical data

WITH target_carriers AS (
  SELECT v.sample_id, v.reference_name, v.start, v.genotype,
         json_extract_scalar(v.attributes, '$.gene') AS gene_symbol,
         json_extract_scalar(v.attributes, '$.clnsig') AS clinical_significance
  FROM genomics_delta.variants v
  WHERE v.reference_name = 'chr21' 
    AND v.start = 25891796 
    AND v.genotype IN ('0/1', '1/1')
)
SELECT p.person_id, p.sample_id, p.year_of_birth,
       tc.gene_symbol, tc.clinical_significance, tc.genotype,
       co.condition_concept_id, co.condition_start_date
FROM clinical_omop.person p
INNER JOIN target_carriers tc ON p.sample_id = tc.sample_id
LEFT JOIN clinical_omop.condition_occurrence co ON p.person_id = co.person_id;
