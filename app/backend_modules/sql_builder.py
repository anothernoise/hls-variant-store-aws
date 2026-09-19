"""
Dialect-aware SQL generator for AWS Genomic Variant Store.
Supports PostgreSQL (Aurora/RDS) and Presto/Trino (Amazon Athena).
"""

import re
from typing import Any, Dict

VALID_GENES = {"APP", "SOD1", "BRCA1"}
IDENTIFIER_REGEX = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def sanitize_identifier(val: str, default: str = "variants", strict: bool = False) -> str:
    """Sanitizes table or column identifiers to prevent SQL injection."""
    if not val or not IDENTIFIER_REGEX.match(val):
        if strict:
            raise ValueError(f"Invalid SQL identifier: {val}")
        return default
    return val


def validate_gene(val: str, strict: bool = True) -> str:
    """Validates gene symbol against permitted genomic targets."""
    cleaned = (val or "").strip().upper()
    if cleaned in VALID_GENES:
        return cleaned
    if strict:
        raise ValueError(f"Invalid gene target '{val}'. Allowed targets: {sorted(list(VALID_GENES))}")
    return "APP"


class SqlBuilder:
    validate_gene = staticmethod(validate_gene)
    sanitize_identifier = staticmethod(sanitize_identifier)
    @staticmethod
    def build_engine_sql(
        engine_config: Dict[str, Any],
        engine_name: str,
        query_kind: str = "af",
        gene: str = "APP"
    ) -> str:
        """Generates dialect-accurate SQL targeting the specific backend engine and database."""
        db_name = engine_config.get("database", "genomics_custom_iceberg")
        tbl_name = sanitize_identifier(engine_config.get("table_name", "variants"), default="variants")
        engine_id = engine_config.get("id", engine_name.lower().replace(" ", "_"))
        safe_gene = validate_gene(gene)

        is_postgres = "PostgreSQL" in engine_name or "postgres" in db_name.lower()

        if is_postgres:
            if query_kind == "af":
                return (
                    f"SELECT '{engine_id}' AS engine, reference_name, start, reference_bases, alternate_bases, "
                    "COUNT(DISTINCT sample_id) AS total_cohort_samples, "
                    "COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS alt_carrier_count, "
                    "ROUND(CAST(COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS numeric) / "
                    "CAST(COUNT(DISTINCT sample_id) AS numeric), 4) AS carrier_frequency, "
                    "attributes->>'gene' AS gene_symbol, "
                    "attributes->>'clnsig' AS clinical_significance "
                    "FROM variants "
                    "GROUP BY reference_name, start, reference_bases, alternate_bases, "
                    "attributes->>'gene', attributes->>'clnsig' "
                    "ORDER BY alt_carrier_count DESC LIMIT 10;"
                )
            elif query_kind == "carriers":
                return (
                    "SELECT sample_id, reference_name, start, reference_bases, alternate_bases, "
                    "genotype, dp, gq, allele_depth, engine, "
                    "attributes->>'gene' AS gene_symbol, "
                    "attributes->>'clnsig' AS clinical_significance "
                    "FROM variants "
                    "WHERE reference_name = 'chr21' AND start = 25891796 AND genotype IN ('0/1', '1/1');"
                )
            elif query_kind == "burden":
                return (
                    f"SELECT v.sample_id, v.attributes->>'gene' AS gene_symbol, "
                    f"COUNT(DISTINCT v.start) AS distinct_variant_sites, "
                    f"SUM(CASE WHEN v.genotype = '0/1' THEN 1 WHEN v.genotype = '1/1' THEN 2 ELSE 0 END) AS total_alt_allele_burden "
                    f"FROM variants v "
                    f"WHERE v.reference_name = 'chr21' AND v.genotype IN ('0/1', '1/1') "
                    f"AND v.attributes->>'gene' = '{safe_gene}' "
                    f"GROUP BY v.sample_id, v.attributes->>'gene';"
                )
            else:  # omop
                return (
                    "WITH target_carriers AS ( "
                    "  SELECT v.sample_id, v.reference_name, v.start, v.genotype, "
                    "         v.attributes->>'gene' AS gene_symbol, "
                    "         v.attributes->>'clnsig' AS clinical_significance "
                    "  FROM variants v "
                    "  WHERE v.reference_name = 'chr21' AND v.start = 25891796 AND v.genotype IN ('0/1', '1/1') "
                    ") "
                    "SELECT p.person_id, p.sample_id, p.year_of_birth, tc.gene_symbol, tc.clinical_significance, tc.genotype, "
                    "       co.condition_concept_id, co.condition_start_date "
                    "FROM person p "
                    "INNER JOIN target_carriers tc ON p.sample_id = tc.sample_id "
                    "LEFT JOIN condition_occurrence co ON p.person_id = co.person_id;"
                )

        # Presto/Trino (Amazon Athena) engines
        # Cleanly resolve S3 Tables and Athena catalogs
        if "/" in db_name:
            # S3 Tables / custom namespace syntax
            parts = [sanitize_identifier(p) for p in db_name.split("/") if p]
            clean_db = ".".join(parts)
            table_ref = f"{clean_db}.{tbl_name}"
        else:
            clean_db = sanitize_identifier(db_name, default="genomics_custom_iceberg")
            table_ref = f"{clean_db}.{tbl_name}"

        if query_kind == "af":
            return (
                f"SELECT '{engine_id}' AS engine, reference_name, start, reference_bases, alternate_bases, "
                "COUNT(DISTINCT sample_id) AS total_cohort_samples, "
                "COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS alt_carrier_count, "
                "ROUND(CAST(COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS double) / "
                "CAST(COUNT(DISTINCT sample_id) AS double), 4) AS carrier_frequency, "
                "json_extract_scalar(attributes, '$.gene') AS gene_symbol, "
                "json_extract_scalar(attributes, '$.clnsig') AS clinical_significance "
                f"FROM {table_ref} "
                "GROUP BY reference_name, start, reference_bases, alternate_bases, "
                "json_extract_scalar(attributes, '$.gene'), json_extract_scalar(attributes, '$.clnsig') "
                "ORDER BY alt_carrier_count DESC LIMIT 10;"
            )
        elif query_kind == "carriers":
            return (
                f"SELECT sample_id, reference_name, start, reference_bases, alternate_bases, "
                f"genotype, dp, gq, allele_depth, engine, "
                f"json_extract_scalar(attributes, '$.gene') AS gene_symbol, "
                f"json_extract_scalar(attributes, '$.clnsig') AS clinical_significance "
                f"FROM {table_ref} "
                f"WHERE reference_name = 'chr21' AND start = 25891796 AND genotype IN ('0/1', '1/1');"
            )
        elif query_kind == "burden":
            return (
                f"SELECT v.sample_id, json_extract_scalar(v.attributes, '$.gene') AS gene_symbol, "
                f"COUNT(DISTINCT v.start) AS distinct_variant_sites, "
                f"SUM(CASE WHEN v.genotype = '0/1' THEN 1 WHEN v.genotype = '1/1' THEN 2 ELSE 0 END) AS total_alt_allele_burden "
                f"FROM {table_ref} v "
                f"WHERE v.reference_name = 'chr21' AND v.genotype IN ('0/1', '1/1') "
                f"AND json_extract_scalar(v.attributes, '$.gene') = '{safe_gene}' "
                f"GROUP BY v.sample_id, json_extract_scalar(v.attributes, '$.gene');"
            )
        else:  # omop
            return (
                f"WITH target_carriers AS ( "
                f"  SELECT v.sample_id, v.reference_name, v.start, v.genotype, "
                f"         json_extract_scalar(v.attributes, '$.gene') AS gene_symbol, "
                f"         json_extract_scalar(v.attributes, '$.clnsig') AS clinical_significance "
                f"  FROM {table_ref} v "
                f"  WHERE v.reference_name = 'chr21' AND v.start = 25891796 AND v.genotype IN ('0/1', '1/1') "
                f") "
                f"SELECT p.person_id, p.sample_id, p.year_of_birth, tc.gene_symbol, tc.clinical_significance, tc.genotype, "
                f"       co.condition_concept_id, co.condition_start_date "
                f"FROM clinical_omop.person p "
                f"INNER JOIN target_carriers tc ON p.sample_id = tc.sample_id "
                f"LEFT JOIN clinical_omop.condition_occurrence co ON p.person_id = co.person_id;"
            )
