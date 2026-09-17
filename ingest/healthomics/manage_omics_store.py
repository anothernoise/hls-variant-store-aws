#!/usr/bin/env python3
"""
AWS HealthOmics Variant Store Lifecycle & Ingestion Manager.
Implements modern AWS HealthOmics best practices:
  - Reference Store management (GRCh38 coordinate systems).
  - KMS CMK integration.
  - Variant Store creation and schema mapping.
  - Asynchronous VCF Import Job dispatching and polling.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("healthomics-manager")

DEFAULT_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))


def run_aws_cli(args: List[str], region: str = DEFAULT_REGION) -> Tuple[int, str, str]:
    """Execute AWS CLI command safely with region parameter."""
    cmd = ["aws"] + args
    if "--region" not in args:
        cmd.extend(["--region", region])
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 1, "", "aws CLI binary not found"


def list_variant_stores() -> List[Dict[str, Any]]:
    """List all AWS HealthOmics variant stores in the current region."""
    code, out, err = run_aws_cli(["omics", "list-variant-stores", "--output", "json"])
    if code != 0:
        logger.error("Failed to list variant stores: %s", err)
        return []
    return json.loads(out).get("variantStores", [])


def get_or_create_reference_store(name: str = "hls_reference_store") -> Optional[str]:
    """Retrieve or create an AWS HealthOmics Reference Store."""
    code, out, err = run_aws_cli(["omics", "list-reference-stores", "--output", "json"])
    if code == 0 and out:
        stores = json.loads(out).get("referenceStores", [])
        for s in stores:
            if s.get("name") == name:
                logger.info("Found existing Reference Store: %s (ARN: %s)", name, s["arn"])
                return s["arn"]

    logger.info("Creating new HealthOmics Reference Store: %s", name)
    c_code, c_out, c_err = run_aws_cli([
        "omics", "create-reference-store",
        "--name", name,
        "--description", "Genomic coordinate reference store for HLS Variant Store",
        "--output", "json"
    ])
    if c_code != 0:
        logger.error("Failed to create reference store: %s", c_err)
        return None
    res = json.loads(c_out)
    return res.get("arn")


def create_variant_store(name: str, reference_arn: str, kms_key_arn: Optional[str] = None) -> Optional[str]:
    """Create a new AWS HealthOmics Variant Store."""
    logger.info("Creating HealthOmics Variant Store: %s with Reference: %s", name, reference_arn)
    cmd = [
        "omics", "create-variant-store",
        "--name", name,
        "--reference", f"referenceArn={reference_arn}",
        "--output", "json"
    ]
    if kms_key_arn:
        cmd.extend(["--sse-config", f"type=KMS,keyArn={kms_key_arn}"])

    code, out, err = run_aws_cli(cmd)
    if code != 0:
        logger.error("Failed to create variant store: %s", err)
        return None

    res = json.loads(out)
    logger.info("Variant store creation initiated. ID: %s (Status: %s)", res.get("id"), res.get("status"))
    return res.get("id")


def start_variant_import_job(store_name: str, role_arn: str, s3_vcf_uri: str) -> Optional[str]:
    """Trigger an asynchronous variant import job from S3."""
    logger.info("Starting VCF import job for store '%s' from %s", store_name, s3_vcf_uri)
    cmd = [
        "omics", "start-variant-import-job",
        "--destination-name", store_name,
        "--role-arn", role_arn,
        "--items", json.dumps([{"source": s3_vcf_uri}]),
        "--output", "json"
    ]
    code, out, err = run_aws_cli(cmd)
    if code != 0:
        logger.error("Failed to start variant import job: %s", err)
        return None

    job_id = json.loads(out).get("jobId")
    logger.info("Import job started successfully. Job ID: %s", job_id)
    return job_id


def main():
    parser = argparse.ArgumentParser(description="AWS HealthOmics Variant Store Manager")
    parser.add_argument("--action", choices=["list", "status", "create-store", "import-vcf"], default="list")
    parser.add_argument("--store-name", default="hls_variant_store_dev")
    parser.add_argument("--reference-arn", default=None)
    parser.add_argument("--kms-key-arn", default=None)
    parser.add_argument("--vcf-s3-uri", default=None)
    parser.add_argument("--role-arn", default=None)

    args = parser.parse_args()

    if args.action == "list" or args.action == "status":
        stores = list_variant_stores()
        print(f"\nDiscovered {len(stores)} HealthOmics Variant Store(s):")
        for s in stores:
            print(f" - Name: {s.get('name')} | ID: {s.get('id')} | Status: {s.get('status')} | Created: {s.get('creationTime')}")
        print()

    elif args.action == "create-store":
        ref_arn = args.reference_arn
        if not ref_arn:
            ref_arn = get_or_create_reference_store()
        if ref_arn:
            create_variant_store(args.store_name, ref_arn, kms_key_arn=args.kms_key_arn)

    elif args.action == "import-vcf":
        if not args.vcf_s3_uri or not args.role_arn:
            logger.error("--vcf-s3-uri and --role-arn are required for import-vcf action")
            sys.exit(1)
        start_variant_import_job(args.store_name, args.role_arn, args.vcf_s3_uri)


if __name__ == "__main__":
    from typing import Tuple
    main()
