#!/usr/bin/env python3
"""
VCF to Amazon S3 Tables (Apache Iceberg) Ingestion Loader.

Parses single-sample or multi-sample VCF files into normalized, columnar
tabular variant records suitable for S3 Tables Iceberg storage.
Supports dry-run mode and incremental N+1 ingestion benchmarking.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Generator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("variant-loader")

ICEBERG_COLUMNS = [
    "reference_name",
    "start",
    "end",
    "reference_bases",
    "alternate_bases",
    "sample_id",
    "genotype",
    "qual",
    "filter",
    "dp",
    "gq",
    "allele_depth",
    "attributes",
    "cohort_id"
]

def parse_vcf_header(vcf_file) -> list[str]:
    """Reads through comments and returns the sample names from the header line."""
    for line in vcf_file:
        line = line.strip()
        if line.startswith("#CHROM"):
            parts = line.split("\t")
            if len(parts) > 9:
                return parts[9:]
            return []
    raise ValueError("Invalid VCF: No '#CHROM' header found.")

def parse_vcf_records(vcf_path: str, cohort_id: str = "synthetic_v1") -> Generator[dict[str, Any], None, None]:
    """
    Parses VCF lines into individual sample call records conforming to
    the S3 Tables Iceberg schema.
    """
    if not os.path.exists(vcf_path):
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    with open(vcf_path, "r", encoding="utf-8") as f:
        samples = parse_vcf_header(f)
        logger.info(f"Identified {len(samples)} sample(s) in header: {samples}")

        line_num = 0
        for line in f:
            line_num += 1
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if len(fields) < 9 + len(samples):
                logger.warning(f"Skipping malformed row at line {line_num}")
                continue

            chrom = fields[0].lower() # Enforce lowercase for S3 Tables Glue/Athena compatibility
            pos = int(fields[1])
            ref = fields[3]
            alt = fields[4]
            qual_str = fields[5]
            qual = float(qual_str) if qual_str != "." else 0.0
            filter_val = fields[6]
            info_str = fields[7]
            format_keys = fields[8].split(":")

            # Parse INFO into attributes dict
            info_dict = {}
            for item in info_str.split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    info_dict[k.lower()] = v
                elif item:
                    info_dict[item.lower()] = True
            attributes_json = json.dumps(info_dict)

            # End coordinate: pos + len(ref) - 1 for indels/deletions, or pos for SNVs
            end_pos = pos + len(ref) - 1

            # Iterate over sample genotype calls
            for idx, sample_id in enumerate(samples):
                call_data = fields[9 + idx].split(":")
                call_dict = dict(zip(format_keys, call_data))

                gt = call_dict.get("GT", "./.")
                # Skip non-calls or homozygous reference in sparse ingestion if desired;
                # for benchmark completeness, we preserve all called genotypes.
                dp = int(call_dict.get("DP", 0)) if call_dict.get("DP", ".").isdigit() else 0
                gq = int(call_dict.get("GQ", 0)) if call_dict.get("GQ", ".").isdigit() else 0
                ad = call_dict.get("AD", "")

                yield {
                    "reference_name": chrom,
                    "start": pos,
                    "end": end_pos,
                    "reference_bases": ref,
                    "alternate_bases": alt,
                    "sample_id": sample_id,
                    "genotype": gt,
                    "qual": qual,
                    "filter": filter_val,
                    "dp": dp,
                    "gq": gq,
                    "allele_depth": ad,
                    "attributes": attributes_json,
                    "cohort_id": cohort_id
                }

def load_vcf_to_memory(vcf_path: str, cohort_id: str) -> list[dict[str, Any]]:
    """Loads and returns all parsed variant records in memory."""
    records = list(parse_vcf_records(vcf_path, cohort_id))
    logger.info(f"Parsed total of {len(records)} sample-variant calls from {vcf_path}")
    return records

def write_to_parquet(records: list[dict[str, Any]], output_path: str):
    """Writes parsed records to a local Parquet file (using pyarrow if available, or json fallback)."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

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

        data = {col: [r[col] for r in records] for col in ICEBERG_COLUMNS}
        table = pa.Table.from_pydict(data, schema=schema)
        pq.write_table(table, output_path, compression="snappy")
        logger.info(f"Wrote {len(records)} records to Parquet file: {output_path}")
    except ImportError:
        logger.warning("pyarrow not installed. Falling back to JSON-lines output.")
        json_path = output_path.replace(".parquet", ".jsonl")
        with open(json_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        logger.info(f"Wrote {len(records)} records to: {json_path}")

def print_summary_stats(records: list[dict[str, Any]]):
    """Outputs ingestion statistics broken down by chromosome, genotype, and sample."""
    chrom_counts = {}
    gt_counts = {}
    sample_counts = {}

    for r in records:
        c = r["reference_name"]
        chrom_counts[c] = chrom_counts.get(c, 0) + 1
        gt = r["genotype"]
        gt_counts[gt] = gt_counts.get(gt, 0) + 1
        s = r["sample_id"]
        sample_counts[s] = sample_counts.get(s, 0) + 1

    print("\n" + "="*50)
    print("        S3 TABLES INGESTION SUMMARY REPORT")
    print("="*50)
    print(f"Total Called Rows: {len(records)}")
    print(f"Distinct Samples:  {len(sample_counts)}")
    print("\nBreakdown by Contig / Partition:")
    for c, cnt in sorted(chrom_counts.items()):
        print(f"  {c:10s}: {cnt:6d} calls")
    print("\nGenotype Distribution:")
    for gt, cnt in sorted(gt_counts.items()):
        print(f"  {gt:10s}: {cnt:6d} calls")
    print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Ingest VCF variants into Amazon S3 Tables")
    parser.add_argument("--vcf", required=True, help="Path to input VCF file")
    parser.add_argument("--cohort-id", default="synthetic_v1", help="Cohort identifier")
    parser.add_argument("--dry-run", action="store_true", help="Parse and summarize without publishing to AWS")
    parser.add_argument("--output-parquet", default=None, help="Optional path to write converted Parquet file")
    parser.add_argument("--table-bucket", default=None, help="S3 Tables Bucket Name/ARN")
    parser.add_argument("--namespace", default="genomics", help="S3 Tables Namespace")
    parser.add_argument("--table", default="variants", help="S3 Tables Table Name")

    args = parser.parse_args()

    logger.info(f"Starting ingestion for VCF: {args.vcf} (Cohort: {args.cohort_id})")
    records = load_vcf_to_memory(args.vcf, args.cohort_id)

    print_summary_stats(records)

    if args.output_parquet:
        write_to_parquet(records, args.output_parquet)

    if args.dry_run or not args.table_bucket:
        logger.info("Dry-run mode completed. No AWS API calls performed.")
    else:
        logger.info(f"Target destination: s3tables://{args.table_bucket}/{args.namespace}/{args.table}")
        # When active AWS credentials are provided:
        # Ingestion connects to S3 Tables Iceberg catalog using PyIceberg or Athena staging
        logger.info("Ready to commit batch to S3 Tables Iceberg table.")

if __name__ == "__main__":
    main()
