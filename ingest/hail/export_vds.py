#!/usr/bin/env python3
"""
Hail VDS (Variant Dataset) Exporter for Genomic Variants.
Simulates Hail's split-dataset representation:
  - Variant Data (VD): Sparse Matrix of alternate and rare genotype calls.
  - Reference Data (RD): Blocked non-variant / homozygous reference intervals.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ingest.s3tables.load_variants import parse_vcf_records

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hail-vds-exporter")


def export_hail_vds_components(vcf_path: str, output_dir: str) -> Tuple[int, int]:
    records = list(parse_vcf_records(vcf_path))
    logger.info("Parsed %d calls for Hail VDS export", len(records))

    variant_data: List[Dict[str, Any]] = []
    reference_data: List[Dict[str, Any]] = []

    for r in records:
        gt = r["genotype"]
        entry = {
            "locus": f"{r['reference_name']}:{r['start']}",
            "alleles": [r["reference_bases"], r["alternate_bases"]],
            "sample_id": r["sample_id"],
            "dp": r["dp"],
            "gq": r["gq"],
            "ad": [int(x) for x in r["allele_depth"].split(",") if x.isdigit()]
        }

        if gt in ("0/1", "1/1"):
            entry["call"] = gt
            entry["info"] = json.loads(r["attributes"])
            variant_data.append(entry)
        else:
            # Homozygous reference or non-variant block
            entry["call"] = "0/0"
            reference_data.append(entry)

    vd_dir = os.path.join(output_dir, "variant_data")
    rd_dir = os.path.join(output_dir, "reference_data")
    os.makedirs(vd_dir, exist_ok=True)
    os.makedirs(rd_dir, exist_ok=True)

    with open(os.path.join(vd_dir, "part-00000.json"), "w", encoding="utf-8") as f:
        json.dump(variant_data, f, indent=2)

    with open(os.path.join(rd_dir, "part-00000.json"), "w", encoding="utf-8") as f:
        json.dump(reference_data, f, indent=2)

    # Hail metadata descriptor
    vds_metadata = {
        "version": "v1.0",
        "reference_genome": "GRCh38",
        "variant_data_rows": len(variant_data),
        "reference_data_rows": len(reference_data)
    }
    with open(os.path.join(output_dir, "vds_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(vds_metadata, f, indent=2)

    logger.info("Exported %d variant rows and %d reference rows to %s", len(variant_data), len(reference_data), output_dir)
    return len(variant_data), len(reference_data)


def main():
    parser = argparse.ArgumentParser(description="Hail VDS Exporter for Genomic Variants")
    parser.add_argument("--vcf", required=True, help="Input VCF file")
    parser.add_argument("--output-dir", default="custom_hail_warehouse", help="Target output directory")
    args = parser.parse_args()

    vd_count, rd_count = export_hail_vds_components(args.vcf, args.output_dir)
    print(f"Hail VDS Export Complete: {vd_count} variant calls, {rd_count} reference intervals in {args.output_dir}")


if __name__ == "__main__":
    from typing import Tuple
    main()
