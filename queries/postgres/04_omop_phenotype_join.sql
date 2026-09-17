-- PostgreSQL / Amazon Aurora: Genotype ↔ OMOP CDM Join
-- Direct relational join with OMOP CDM person and condition_occurrence tables

WITH target_carriers AS (
  SELECT v.sample_id, v.reference_name, v.start, v.genotype,
         v.attributes->>'gene' AS gene_symbol,
         v.attributes->>'clnsig' AS clinical_significance
  FROM variants v
  WHERE v.reference_name = 'chr21' 
    AND v.start = 25891796 
    AND v.genotype IN ('0/1', '1/1')
)
SELECT p.person_id, p.sample_id, p.year_of_birth,
       tc.gene_symbol, tc.clinical_significance, tc.genotype,
       co.condition_concept_id, co.condition_start_date
FROM person p
INNER JOIN target_carriers tc ON p.sample_id = tc.sample_id
LEFT JOIN condition_occurrence co ON p.person_id = co.person_id;
