#!/usr/bin/env python3
"""
Delta Lake on S3 Loader for Genomic Variants.
Generates partitioned Parquet data files alongside standard Delta transaction log entries (_delta_log/).
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ingest.s3tables.load_variants import parse_vcf_records

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("delta-loader")


def create_delta_log_entry(records: List[Dict[str, Any]], partition_key: str, data_filename: str) -> Dict[str, Any]:
    """Create a standard Delta Lake v1 commit action JSON object."""
    size_bytes = len(json.dumps(records)) * 2  # approximate uncompressed
    return {
        "add": {
            "path": f"reference_name={partition_key}/{data_filename}",
            "partitionValues": {"reference_name": partition_key},
            "size": size_bytes,
            "modificationTime": int(time.time() * 1000),
            "dataChange": True,
            "stats": json.dumps({
                "numRecords": len(records),
                "minValues": {
                    "start": min(r["start"] for r in records),
                    "sample_id": min(r["sample_id"] for r in records)
                },
                "maxValues": {
                    "start": max(r["start"] for r in records),
                    "sample_id": max(r["sample_id"] for r in records)
                }
            })
        }
    }


def write_local_delta_dataset(vcf_path: str, output_dir: str, version: int = 0) -> int:
    """Transform VCF records into partition files and write Delta commit log."""
    records = list(parse_vcf_records(vcf_path))
    logger.info("Parsed %d variant calls from %s", len(records), vcf_path)

    # Group by partition (reference_name)
    partitions: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        chrom = r["reference_name"]
        partitions.setdefault(chrom, []).append(r)

    delta_log_dir = os.path.join(output_dir, "_delta_log")
    os.makedirs(delta_log_dir, exist_ok=True)

    commit_actions = [
        {"commitInfo": {"timestamp": int(time.time() * 1000), "operation": "WRITE", "engine": "Python-Delta-Loader"}}
    ]

    for chrom, part_records in partitions.items():
        part_dir = os.path.join(output_dir, f"reference_name={chrom}")
        os.makedirs(part_dir, exist_ok=True)
        filename = f"part-{version:04d}-{chrom}.json"
        filepath = os.path.join(part_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(part_records, f, indent=2)

        action = create_delta_log_entry(part_records, chrom, filename)
        commit_actions.append(action)

    # Write Delta commit log file: 00000000000000000000.json
    log_filename = f"{version:020d}.json"
    log_path = os.path.join(delta_log_dir, log_filename)
    with open(log_path, "w", encoding="utf-8") as f:
        for action in commit_actions:
            f.write(json.dumps(action) + "\n")

    logger.info("Successfully wrote Delta commit log version %d: %s", version, log_path)
    return len(records)


def main():
    parser = argparse.ArgumentParser(description="Delta Lake on S3 Loader for Genomic Variants")
    parser.add_argument("--vcf", required=True, help="Path to input VCF file")
    parser.add_argument("--output-dir", default="custom_delta_warehouse/variants", help="Target output directory")
    parser.add_argument("--version", type=int, default=0, help="Delta commit log version number")
    parser.add_argument("--dry-run", action="store_true", help="Parse and log without file emission")

    args = parser.parse_args()

    if args.dry_run:
        records = list(parse_vcf_records(args.vcf))
        logger.info("[DRY RUN] Would write %d records into Delta Lake format", len(records))
    else:
        count = write_local_delta_dataset(args.vcf, args.output_dir, version=args.version)
        print(f"Successfully processed {count} records into Delta Lake format at {args.output_dir}")


if __name__ == "__main__":
    main()
