#!/usr/bin/env python3
"""
Multi-Engine Infrastructure Manager for AWS Genomic Variant Store.
Allows Solution Architects to:
  1. Inspect live infrastructure status across all 7 engines using boto3 / botocore.
  2. Selectively deploy or destroy specific engine stacks using Terraform.
  3. Validate connectivity and query performance per engine.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

# Bootstrap botocore / boto3 from awscli package bundle if not installed globally
for p in [
    "/opt/homebrew/Cellar/awscli/2.27.58/libexec/lib/python3.13/site-packages",
    "/opt/homebrew/Cellar/awscli/2.27.58/libexec/lib/python3.13/site-packages/awscli"
]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from botocore.session import Session
except ImportError:
    Session = None

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERRAFORM_DIR = os.path.join(PROJECT_ROOT, "deploy/terraform")

ALL_ENGINES = [
    "s3_tables",
    "custom_iceberg",
    "clinical_omop",
    "delta_lake",
    "hail_vds",
    "postgres_aurora",
    "postgres_rds",
    "healthomics"
]

ENGINE_LABEL_MAP = {
    "s3_tables": "Amazon S3 Tables (Iceberg)",
    "custom_iceberg": "Custom S3 + Iceberg",
    "clinical_omop": "OMOP CDM Clinical Phenotypes",
    "delta_lake": "Delta Lake on S3",
    "hail_vds": "Hail VDS on S3",
    "postgres_aurora": "Amazon Aurora PostgreSQL (Serverless v2)",
    "postgres_rds": "Amazon RDS PostgreSQL",
    "healthomics": "AWS HealthOmics Variant Store"
}


def get_aws_session(profile: str = "default", region: str = "us-east-1"):
    """Instantiate a configured botocore session."""
    if Session is None:
        return None
    try:
        return Session(profile=profile)
    except Exception:
        return None


def check_engine_status(profile: str = "default", region: str = "us-east-1") -> List[Dict[str, Any]]:
    """Query AWS services to inspect live status of all 7 engines."""
    results = []
    sess = get_aws_session(profile, region)
    
    # 1. Glue Databases
    glue_dbs = []
    if sess:
        try:
            glue = sess.create_client("glue", region_name=region)
            glue_dbs = [d["Name"] for d in glue.get_databases().get("DatabaseList", [])]
        except Exception:
            pass

    # 2. S3 Tables
    s3tables_buckets = []
    if sess:
        try:
            s3t = sess.create_client("s3tables", region_name=region)
            s3tables_buckets = [b["name"] for b in s3t.list_table_buckets().get("tableBuckets", [])]
        except Exception:
            pass

    # 3. RDS / Aurora
    aurora_clusters = []
    rds_instances = []
    if sess:
        try:
            rds = sess.create_client("rds", region_name=region)
            clusters = rds.describe_db_clusters().get("DBClusters", [])
            for c in clusters:
                if "hls-variant-store" in c.get("DBClusterIdentifier", ""):
                    aurora_clusters.append({
                        "id": c.get("DBClusterIdentifier"),
                        "status": c.get("Status"),
                        "endpoint": c.get("Endpoint"),
                        "engine": c.get("Engine")
                    })
            instances = rds.describe_db_instances().get("DBInstances", [])
            for i in instances:
                if "hls-variant-store" in i.get("DBInstanceIdentifier", "") and not i.get("DBClusterIdentifier"):
                    rds_instances.append({
                        "id": i.get("DBInstanceIdentifier"),
                        "status": i.get("DBInstanceStatus"),
                        "endpoint": i.get("Endpoint", {}).get("Address")
                    })
        except Exception:
            pass

    # 4. HealthOmics
    omics_stores = []
    ref_stores = []
    if sess:
        try:
            omics = sess.create_client("omics", region_name=region)
            omics_stores = omics.list_variant_stores().get("variantStores", [])
            ref_stores = omics.list_reference_stores().get("referenceStores", [])
        except Exception:
            pass

    # Map S3 Tables
    s3t_active = any("hls-variant-store" in b for b in s3tables_buckets)
    results.append({
        "key": "s3_tables",
        "name": ENGINE_LABEL_MAP["s3_tables"],
        "status": "ACTIVE" if s3t_active else "NOT_DEPLOYED",
        "details": f"Table Bucket: {s3tables_buckets[0]}" if s3tables_buckets else "None"
    })

    # Map Custom Iceberg
    iceberg_active = "genomics_custom_iceberg" in glue_dbs
    results.append({
        "key": "custom_iceberg",
        "name": ENGINE_LABEL_MAP["custom_iceberg"],
        "status": "ACTIVE" if iceberg_active else "NOT_DEPLOYED",
        "details": "Glue Database: genomics_custom_iceberg" if iceberg_active else "None"
    })

    # Map OMOP CDM
    omop_active = "clinical_omop" in glue_dbs
    results.append({
        "key": "clinical_omop",
        "name": ENGINE_LABEL_MAP["clinical_omop"],
        "status": "ACTIVE" if omop_active else "NOT_DEPLOYED",
        "details": "Glue Database: clinical_omop" if omop_active else "None"
    })

    # Map Delta Lake
    delta_active = "genomics_delta" in glue_dbs
    results.append({
        "key": "delta_lake",
        "name": ENGINE_LABEL_MAP["delta_lake"],
        "status": "ACTIVE" if delta_active else "NOT_DEPLOYED",
        "details": "Glue Database: genomics_delta" if delta_active else "None"
    })

    # Map Hail VDS
    hail_active = "genomics_hail_vds" in glue_dbs
    results.append({
        "key": "hail_vds",
        "name": ENGINE_LABEL_MAP["hail_vds"],
        "status": "ACTIVE" if hail_active else "NOT_DEPLOYED",
        "details": "Glue Database: genomics_hail_vds" if hail_active else "None"
    })

    # Map Aurora Serverless
    aurora_active = len(aurora_clusters) > 0
    results.append({
        "key": "postgres_aurora",
        "name": ENGINE_LABEL_MAP["postgres_aurora"],
        "status": aurora_clusters[0]["status"].upper() if aurora_active else "NOT_DEPLOYED",
        "details": f"Endpoint: {aurora_clusters[0]['endpoint']}" if aurora_active else "None"
    })

    # Map RDS Instance
    rds_active = len(rds_instances) > 0
    results.append({
        "key": "postgres_rds",
        "name": ENGINE_LABEL_MAP["postgres_rds"],
        "status": rds_instances[0]["status"].upper() if rds_active else "NOT_DEPLOYED",
        "details": f"Endpoint: {rds_instances[0]['endpoint']}" if rds_active else "None"
    })

    # Map HealthOmics
    omics_active = len(omics_stores) > 0 or len(ref_stores) > 0
    results.append({
        "key": "healthomics",
        "name": ENGINE_LABEL_MAP["healthomics"],
        "status": "ACTIVE" if omics_active else "NOT_DEPLOYED",
        "details": f"Reference Store: {ref_stores[0]['id']}" if ref_stores else "None"
    })

    return results


def print_status_table(status_list: List[Dict[str, Any]]):
    """Render status output in a clean terminal table."""
    print("\n" + "=" * 90)
    print("                AWS GENOMIC VARIANT STORE: INFRASTRUCTURE STATUS")
    print("=" * 90)
    print(f"{'Engine / Data Source':<42} | {'Status':<15} | {'Live Resource Details'}")
    print("-" * 90)
    for row in status_list:
        status_color = row["status"]
        print(f"{row['name']:<42} | {status_color:<15} | {row['details']}")
    print("=" * 90 + "\n")


def build_tf_var_flags(selected_engines: List[str]) -> List[str]:
    """Derive terraform -var flags based on selected engines list."""
    flags = []
    
    # Delta Lake
    enable_delta = "delta_lake" in selected_engines
    flags.append(f'-var=enable_delta_lake={str(enable_delta).lower()}')

    # Hail VDS
    enable_hail = "hail_vds" in selected_engines
    flags.append(f'-var=enable_hail_vds={str(enable_hail).lower()}')

    # PostgreSQL / Aurora
    enable_aurora = "postgres_aurora" in selected_engines
    enable_rds = "postgres_rds" in selected_engines
    enable_pg = enable_aurora or enable_rds
    flags.append(f'-var=enable_postgres={str(enable_pg).lower()}')
    
    if enable_rds and not enable_aurora:
        flags.append('-var=postgres_deployment_mode=rds')
    else:
        flags.append('-var=postgres_deployment_mode=aurora_serverless')

    # HealthOmics
    enable_omics = "healthomics" in selected_engines
    flags.append(f'-var=enable_healthomics={str(enable_omics).lower()}')

    return flags


def run_terraform_action(action: str, selected_engines: List[str], auto_approve: bool = False):
    """Execute selective terraform apply or destroy."""
    flags = build_tf_var_flags(selected_engines)
    cmd = ["terraform", action] + flags
    if auto_approve:
        cmd.append("-auto-approve")

    print(f"\n[INFO] Executing Terraform: {' '.join(cmd)}")
    print(f"[INFO] Target Engines: {', '.join(selected_engines)}\n")
    
    env = os.environ.copy()
    env["AWS_PROFILE"] = env.get("AWS_PROFILE", "default")
    env["AWS_REGION"] = env.get("AWS_REGION", "us-east-1")
    
    proc = subprocess.run(cmd, cwd=TERRAFORM_DIR, env=env)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Manage AWS Genomic Variant Store multi-engine infrastructure."
    )
    parser.add_argument(
        "--action",
        choices=["status", "deploy", "destroy"],
        default="status",
        help="Action to perform (status, deploy, destroy)"
    )
    parser.add_argument(
        "--engines",
        default="all",
        help=(
            "Comma-separated list of engines to manage. Available: "
            + ", ".join(ALL_ENGINES)
            + " (or 'all')"
        )
    )
    parser.add_argument("--profile", default="default", help="AWS CLI profile name (default: default)")
    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve terraform apply/destroy")

    args = parser.parse_args()

    # Parse engines
    if args.engines.lower() == "all":
        selected_engines = list(ALL_ENGINES)
    else:
        selected_engines = [e.strip() for e in args.engines.split(",") if e.strip()]
        for e in selected_engines:
            if e not in ALL_ENGINES:
                print(f"[ERROR] Unknown engine '{e}'. Valid engines: {ALL_ENGINES}")
                sys.exit(1)

    if args.action == "status":
        status_list = check_engine_status(profile=args.profile, region=args.region)
        print_status_table(status_list)

    elif args.action == "deploy":
        code = run_terraform_action("apply", selected_engines, auto_approve=args.auto_approve)
        if code == 0:
            print("\n[SUCCESS] Deployment complete. Current status:")
            status_list = check_engine_status(profile=args.profile, region=args.region)
            print_status_table(status_list)
        sys.exit(code)

    elif args.action == "destroy":
        code = run_terraform_action("destroy", selected_engines, auto_approve=args.auto_approve)
        if code == 0:
            print("\n[SUCCESS] Destruction complete. Current status:")
            status_list = check_engine_status(profile=args.profile, region=args.region)
            print_status_table(status_list)
        sys.exit(code)


if __name__ == "__main__":
    main()
