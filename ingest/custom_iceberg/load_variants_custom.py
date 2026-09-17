#!/usr/bin/env python3
"""
Custom S3 + Apache Iceberg Ingestion Loader.

Parses single-sample or multi-sample VCF files and writes partition-aligned
columnar data (partitioned by reference_name) into the custom S3 Iceberg warehouse.
Demonstrates non-destructive additive ingest for the N+1 problem.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

# Reuse tested parser logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from ingest.s3tables.load_variants import parse_vcf_records, ICEBERG_COLUMNS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("custom-iceberg-loader")

def partition_records_by_chrom(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Partitions variant records by reference_name (chromosome)."""
    partitions: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        chrom = r["reference_name"]
        if chrom not in partitions:
            partitions[chrom] = []
        partitions[chrom].append(r)
    return partitions

def write_partitioned_dataset(partitions: dict[str, list[dict[str, Any]]], output_dir: str, batch_id: str) -> dict[str, str]:
    """
    Writes partitioned data files to the output directory.
    Uses Hive-style partition directories: reference_name=<chrom>/batch_<id>.parquet (or .jsonl).
    """
    os.makedirs(output_dir, exist_ok=True)
    created_files = {}

    has_pyarrow = False
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        has_pyarrow = True
    except ImportError:
        has_pyarrow = False

    schema = None
    if has_pyarrow:
        schema = pa.schema([
            ("reference_name", pa.string()),
            ("start", pa.int64()),
            ("end", pa.int64()),
            ("reference_bases", pa.string()),
            ("alternate_bases", pa.string()),
            ("sample_id", pa.string()),
            ("genotype", pa.string()),
            ("qual", pa.float64()),
            ("filter", pa.string()),
            ("dp", pa.int32()),
            ("gq", pa.int32()),
            ("allele_depth", pa.string()),
            ("attributes", pa.string()),
            ("cohort_id", pa.string()),
        ])

    for chrom, rows in partitions.items():
        part_dir = os.path.join(output_dir, f"reference_name={chrom}")
        os.makedirs(part_dir, exist_ok=True)

        if has_pyarrow:
            file_name = f"data_batch_{batch_id}.parquet"
            file_path = os.path.join(part_dir, file_name)
            data = {col: [r[col] for r in rows] for col in ICEBERG_COLUMNS}
            table = pa.Table.from_pydict(data, schema=schema)
            pq.write_table(table, file_path, compression="snappy")
        else:
            file_name = f"data_batch_{batch_id}.jsonl"
            file_path = os.path.join(part_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")

        created_files[chrom] = file_path
        logger.info(f"Partition reference_name={chrom}: wrote {len(rows)} calls to {file_path}")

    return created_files

def main():
    parser = argparse.ArgumentParser(description="Ingest VCF variants into Custom S3 + Iceberg table")
    parser.add_argument("--vcf", required=True, help="Path to input VCF file")
    parser.add_argument("--cohort-id", default="synthetic_v1", help="Cohort identifier")
    parser.add_argument("--batch-id", default="001", help="Batch identifier for N+1 append tracking")
    parser.add_argument("--output-dir", default="samples/data/custom_iceberg_warehouse", help="Output directory for staged warehouse data")
    parser.add_argument("--warehouse-bucket", default=None, help="S3 Warehouse Bucket Name")
    parser.add_argument("--dry-run", action="store_true", help="Perform staging and partitioning without S3 upload")

    args = parser.parse_args()

    logger.info(f"Loading {args.vcf} for Custom S3 + Iceberg (Batch: {args.batch_id})")
    records = list(parse_vcf_records(args.vcf, args.cohort_id))
    logger.info(f"Parsed {len(records)} calls from {args.vcf}")

    partitions = partition_records_by_chrom(records)
    created_files = write_partitioned_dataset(partitions, args.output_dir, args.batch_id)

    print("\n" + "="*55)
    print("      CUSTOM S3 + ICEBERG INGESTION REPORT")
    print("="*55)
    print(f"Batch ID:         {args.batch_id}")
    print(f"Total Calls:      {len(records)}")
    print(f"Partitions Count: {len(partitions)}")
    for chrom, path in created_files.items():
        print(f"  reference_name={chrom:6s} -> {os.path.basename(path)}")
    print("="*55 + "\n")

    if args.dry_run or not args.warehouse_bucket:
        logger.info("Dry-run mode complete. Partition files staged locally.")
    else:
        logger.info(f"Ready to sync partition files to s3://{args.warehouse_bucket}/warehouse/variants/")

if __name__ == "__main__":
    main()
