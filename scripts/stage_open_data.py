#!/usr/bin/env python3
"""
Remote AWS Open Data Staging & Catalog Registration Tool.

Stages real-world public datasets from the Registry of Open Data on AWS
directly into project S3 buckets and AWS Glue Catalogs in us-east-1:
  1. Synthea OMOP CDM v5.4: s3://synthea-omop/synthea1k/ -> clinical_data bucket
  2. 1000 Genomes Project: s3://1000genomes/release/20130502/ -> variant warehouse

STRICT LOCAL FOOTPRINT SAFEGUARD:
Data transfers execute directly intra-region S3-to-S3 in us-east-1.
No multi-gigabyte open dataset files are stored in or committed to the local repository.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("open-data-stager")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERRAFORM_DIR = os.path.join(PROJECT_ROOT, "deploy/terraform")

# Public AWS Open Data Source URIs (all in us-east-1)
PUBLIC_SYNTHEA_OMOP_S3 = "s3://synthea-omop/synthea1k"
PUBLIC_1000GENOMES_S3 = "s3://1000genomes/release/20130502"


def get_terraform_outputs() -> Dict[str, str]:
    """Retrieve bucket and database names dynamically from Terraform state."""
    try:
        proc = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=TERRAFORM_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(proc.stdout)
        return {k: v.get("value") for k, v in data.items() if isinstance(v, dict)}
    except Exception as e:
        logger.warning("Could not read Terraform outputs dynamically: %s. Using default resource names.", e)
        return {
            "clinical_omop_data_bucket": "hls-variant-store-clinical-data-dev-79295722",
            "clinical_omop_glue_database": "clinical_omop",
            "custom_iceberg_warehouse_bucket": "hls-variant-store-iceberg-warehouse-dev-79295722",
            "custom_iceberg_glue_database": "genomics_custom_iceberg",
            "delta_lake_warehouse_bucket": "hls-variant-store-dev-79295722-delta-warehouse",
            "delta_lake_glue_database": "genomics_delta",
            "hail_vds_bucket": "hls-variant-store-dev-79295722-hail-vds",
            "hail_vds_glue_database": "genomics_hail_vds",
            "s3tables_table_bucket_name": "hls-variant-store-dev-79295722",
            "athena_workgroup_name": "hls-variant-store-dev"
        }


def check_staging_status(profile: str = "default", region: str = "us-east-1"):
    """Inspects remote S3 buckets to report currently staged Open Data."""
    tf_outputs = get_terraform_outputs()
    clinical_bucket = tf_outputs.get("clinical_omop_data_bucket")
    iceberg_bucket = tf_outputs.get("custom_iceberg_warehouse_bucket")

    print("\n" + "=" * 80)
    print("             REMOTE AWS OPEN DATA STAGING STATUS (us-east-1)")
    print("=" * 80)

    # 1. Synthea OMOP Data
    omop_target = f"s3://{clinical_bucket}/omop"
    print(f"\n[1] Clinical OMOP Dataset Target: {omop_target}")
    cmd = ["aws", "s3", "ls", omop_target, "--recursive", "--human-readable", "--summarize"]
    if profile:
        cmd.extend(["--profile", profile])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            print(proc.stdout.strip())
        else:
            print("  Status: Empty / Not yet staged.")
    except Exception as e:
        print(f"  Error checking S3: {e}")

    # 2. 1000 Genomes Genomic Data
    genomes_target = f"s3://{iceberg_bucket}/open_data_1000genomes"
    print(f"\n[2] 1000 Genomes Staging Target: {genomes_target}")
    cmd_g = ["aws", "s3", "ls", genomes_target, "--recursive", "--human-readable", "--summarize"]
    if profile:
        cmd_g.extend(["--profile", profile])
    try:
        proc_g = subprocess.run(cmd_g, capture_output=True, text=True)
        if proc_g.returncode == 0 and proc_g.stdout.strip():
            print(proc_g.stdout.strip())
        else:
            print("  Status: Empty / Not yet staged.")
    except Exception as e:
        print(f"  Error checking S3: {e}")

    print("=" * 80 + "\n")


def stage_synthea_omop(dry_run: bool = False, profile: str = "default", region: str = "us-east-1"):
    """Copies Synthea 1k OMOP tables directly from public S3 into our clinical data bucket."""
    tf_outputs = get_terraform_outputs()
    clinical_bucket = tf_outputs.get("clinical_omop_data_bucket")
    if not clinical_bucket:
        logger.error("No clinical_omop_data_bucket found in Terraform outputs.")
        return False

    tables = ["person.csv", "condition_occurrence.csv"]
    success = True

    for tbl in tables:
        src = f"{PUBLIC_SYNTHEA_OMOP_S3}/{tbl}"
        folder = tbl.replace(".csv", "")
        dst = f"s3://{clinical_bucket}/omop/{folder}/{tbl}"

        cmd = [
            "aws", "s3", "cp", src, dst,
            "--region", region,
            "--source-region", region,
            "--copy-props", "none"
        ]
        if profile:
            cmd.extend(["--profile", profile])

        logger.info(f"Staging OMOP table: {src} -> {dst}")
        if dry_run:
            print(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
        else:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                logger.info(f"Successfully staged {tbl} to {dst}")
            else:
                logger.error(f"Failed staging {tbl}: {proc.stderr}")
                success = False

    return success


def stage_1000genomes_slice(
    chromosome: str = "chr21",
    dry_run: bool = False,
    profile: str = "default",
    region: str = "us-east-1"
):
    """Stages a 1000 Genomes chromosome callset directly from public S3."""
    tf_outputs = get_terraform_outputs()
    iceberg_bucket = tf_outputs.get("custom_iceberg_warehouse_bucket")
    if not iceberg_bucket:
        logger.error("No custom_iceberg_warehouse_bucket found.")
        return False

    vcf_filename = f"ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
    tbi_filename = f"{vcf_filename}.tbi"

    src_vcf = f"{PUBLIC_1000GENOMES_S3}/{vcf_filename}"
    src_tbi = f"{PUBLIC_1000GENOMES_S3}/{tbi_filename}"
    dst_prefix = f"s3://{iceberg_bucket}/open_data_1000genomes/{chromosome}/"

    logger.info(f"Staging 1000 Genomes callset for {chromosome} to {dst_prefix}")

    for src in [src_vcf, src_tbi]:
        dst = f"{dst_prefix}{os.path.basename(src)}"
        cmd = [
            "aws", "s3", "cp", src, dst,
            "--region", region,
            "--source-region", region,
            "--copy-props", "none"
        ]
        if profile:
            cmd.extend(["--profile", profile])

        if dry_run:
            print(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
        else:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                logger.info(f"Successfully staged {src} -> {dst}")
            else:
                logger.error(f"Failed staging {src}: {proc.stderr}")
                return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Remote AWS Open Data Staging & Lakehouse Performance Preparation"
    )
    parser.add_argument(
        "--action",
        choices=["stage", "status"],
        default="status",
        help="Action to execute: 'status' to inspect remote staging, 'stage' to transfer S3-to-S3"
    )
    parser.add_argument(
        "--dataset",
        choices=["omop", "1000genomes", "all"],
        default="all",
        help="Target dataset to stage (default: all)"
    )
    parser.add_argument(
        "--chromosome",
        default="chr21",
        help="Target chromosome for 1000 Genomes staging (default: chr21)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview S3 intra-region transfer commands without transferring data"
    )
    parser.add_argument(
        "--profile",
        default="default",
        help="AWS profile name (default: default)"
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    if args.action == "status":
        check_staging_status(profile=args.profile, region=args.region)
        return

    if args.action == "stage":
        logger.info(f"Beginning Remote Open Data Staging (Dry-Run: {args.dry_run})")
        if args.dataset in ("omop", "all"):
            stage_synthea_omop(dry_run=args.dry_run, profile=args.profile, region=args.region)
        if args.dataset in ("1000genomes", "all"):
            stage_1000genomes_slice(
                chromosome=args.chromosome,
                dry_run=args.dry_run,
                profile=args.profile,
                region=args.region
            )
        logger.info("Staging command execution completed.")


if __name__ == "__main__":
    main()
