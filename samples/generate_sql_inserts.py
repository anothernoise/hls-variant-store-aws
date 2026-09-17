#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingest.s3tables.load_variants import parse_vcf_records

def generate_insert_sql(vcf_path: str, table_name: str) -> str:
    records = list(parse_vcf_records(vcf_path))
    value_clauses = []
    for r in records:
        # Presto/Trino SQL escapes single quotes by doubling them ''
        attr_sql = r["attributes"].replace("'", "''")
        clause = (
            f"({r['start']}, {r['end']}, '{r['reference_bases']}', '{r['alternate_bases']}', "
            f"'{r['sample_id']}', '{r['genotype']}', {r['qual']}, '{r['filter']}', "
            f"{r['dp']}, {r['gq']}, '{r['allele_depth']}', '{attr_sql}', '{r['cohort_id']}', '{r['reference_name']}')"
        )
        value_clauses.append(clause)

    columns = "start, end_pos, reference_bases, alternate_bases, sample_id, genotype, qual, filter, dp, gq, allele_depth, attributes, cohort_id, reference_name"
    sql = f"INSERT INTO {table_name} ({columns}) VALUES\n" + ",\n".join(value_clauses) + ";"
    return sql

def main():
    b1_sql = generate_insert_sql("samples/data/cohort_batch1_samples1to5.vcf", "genomics_custom_iceberg.variants")
    with open("samples/data/insert_batch1.sql", "w", encoding="utf-8") as f:
        f.write(b1_sql)

    b2_sql = generate_insert_sql("samples/data/cohort_batch2_samples6to10.vcf", "genomics_custom_iceberg.variants")
    with open("samples/data/insert_batch2.sql", "w", encoding="utf-8") as f:
        f.write(b2_sql)

    print("Successfully generated samples/data/insert_batch1.sql and samples/data/insert_batch2.sql")

if __name__ == "__main__":
    main()
