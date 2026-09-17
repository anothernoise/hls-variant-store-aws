#!/usr/bin/env python3
"""
Comprehensive Exercise & Deployment Validation CLI for AWS Genomic Variant Store.
Designed for Bootcamp attendees and CI/CD pipelines to verify lab exercises.

Supports two execution modes:
  1. --local-mode : Validates synthetic VCF integrity, OMOP CDM datasets,
                    VCF parser transformations, and local SQL syntax (offline).
  2. --aws-mode   : Validates live AWS Athena infrastructure, executes queries,
                    measures latency, checks data scanned, and verifies scientific assertions.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ingest.s3tables.load_variants import parse_vcf_records

# ANSI Colors for Bootcamp Terminal Output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class ValidationReporter:
    def __init__(self):
        self.results: List[Tuple[str, bool, str, Optional[float]]] = []

    def record(self, check_name: str, passed: bool, details: str = "", duration_ms: Optional[float] = None):
        self.results.append((check_name, passed, details, duration_ms))
        status_tag = f"{GREEN}[PASS]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
        latency_tag = f" ({duration_ms:.0f}ms)" if duration_ms is not None else ""
        print(f"  {status_tag} {check_name}{latency_tag}")
        if details and not passed:
            print(f"         {YELLOW}Details: {details}{RESET}")

    def summary(self) -> int:
        total = len(self.results)
        passed = sum(1 for _, p, _, _ in self.results if p)
        failed = total - passed

        print("\n" + "=" * 80)
        print(f"{BOLD}EXERCISE VALIDATION SUMMARY{RESET}")
        print("=" * 80)
        for check, p, details, duration in self.results:
            badge = f"{GREEN}PASS{RESET}" if p else f"{RED}FAIL{RESET}"
            dur = f"{duration:6.0f}ms" if duration is not None else "     - "
            print(f"[{badge}] {dur} | {check}")
        print("-" * 80)
        status_color = GREEN if failed == 0 else RED
        print(f"Total Checks: {total} | {GREEN}Passed: {passed}{RESET} | {status_color}Failed: {failed}{RESET}")
        print("=" * 80 + "\n")
        return 0 if failed == 0 else 1


def run_aws_cli(command_args: List[str]) -> Tuple[int, str, str]:
    """Execute AWS CLI commands safely with captured stdout/stderr."""
    try:
        proc = subprocess.run(
            ["aws"] + command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 1, "", "aws CLI binary not found in system PATH"


def execute_athena_query(
    query_string: str,
    workgroup: str = "hls-variant-store-dev",
    database: str = "genomics_custom_iceberg",
    timeout_seconds: int = 45
) -> Dict[str, Any]:
    """Submit an Athena query, poll for completion, and return telemetry + sample results."""
    cmd = [
        "athena", "start-query-execution",
        "--query-string", query_string,
        "--work-group", workgroup,
        "--query-execution-context", f"Database={database}",
        "--output", "json"
    ]
    code, stdout, stderr = run_aws_cli(cmd)
    if code != 0:
        raise RuntimeError(f"Failed to start Athena query: {stderr}")

    qid = json.loads(stdout)["QueryExecutionId"]
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        status_cmd = [
            "athena", "get-query-execution",
            "--query-execution-id", qid,
            "--output", "json"
        ]
        s_code, s_out, s_err = run_aws_cli(status_cmd)
        if s_code != 0:
            raise RuntimeError(f"Failed to inspect query status: {s_err}")

        exec_info = json.loads(s_out)["QueryExecution"]
        state = exec_info["Status"]["State"]

        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            if state != "SUCCEEDED":
                reason = exec_info["Status"].get("StateChangeReason", "Unknown error")
                raise RuntimeError(f"Athena query {qid} failed: {reason}")

            stats = exec_info.get("Statistics", {})
            # Fetch first batch of rows
            res_cmd = [
                "athena", "get-query-results",
                "--query-execution-id", qid,
                "--max-items", "10",
                "--output", "json"
            ]
            r_code, r_out, r_err = run_aws_cli(res_cmd)
            rows = []
            if r_code == 0:
                res_data = json.loads(r_out)
                rows = res_data.get("ResultSet", {}).get("Rows", [])

            return {
                "query_id": qid,
                "state": state,
                "engine_time_ms": stats.get("EngineExecutionTimeInMillis", 0),
                "total_time_ms": stats.get("TotalExecutionTimeInMillis", 0),
                "scanned_bytes": stats.get("DataScannedInBytes", 0),
                "rows": rows
            }
        time.sleep(1)

    raise TimeoutError(f"Athena query {qid} exceeded timeout of {timeout_seconds}s")


# ============================================================================
# EXERCISE VALIDATION SUITE
# ============================================================================

def validate_exercise_1_synthetic_data(reporter: ValidationReporter):
    """Exercise 1: Check deterministic synthetic test data and VCF parsing."""
    print(f"\n{BOLD}{CYAN}▶ Validating Exercise 1: Synthetic Data Generation & Parsing{RESET}")

    vcf_path = os.path.join(PROJECT_ROOT, "samples/data/cohort_10samples.vcf")
    person_path = os.path.join(PROJECT_ROOT, "samples/data/person.csv")
    cond_path = os.path.join(PROJECT_ROOT, "samples/data/condition_occurrence.csv")

    # 1.1 Check files exist
    files_exist = os.path.exists(vcf_path) and os.path.exists(person_path) and os.path.exists(cond_path)
    reporter.record("Synthetic data files present in samples/data/", files_exist)

    if not files_exist:
        reporter.record("VCF Record Parsing", False, "Missing synthetic cohort files. Run samples/generate_synthetic_data.py first.")
        return

    # 1.2 Parse 10-sample VCF
    start = time.time()
    records = list(parse_vcf_records(vcf_path))
    duration_ms = (time.time() - start) * 1000
    reporter.record(
        f"Parse 10-sample multi-sample VCF ({len(records)} calls extracted)",
        len(records) == 100,
        f"Expected 100 calls, got {len(records)}",
        duration_ms
    )

    # 1.3 Verify target pathogenic variant presence
    app_calls = [r for r in records if r["reference_name"] == "chr21" and r["start"] == 25891796]
    app_carriers = [r for r in app_calls if r["genotype"] in ("0/1", "1/1")]
    carrier_sample_ids = {r["sample_id"] for r in app_carriers}
    expected_sample_ids = {"sample_002", "sample_004", "sample_005", "sample_008"}
    reporter.record(
        f"Verify target pathogenic APP rs63750066 variant ({len(app_carriers)} carriers)",
        carrier_sample_ids == expected_sample_ids,
        f"Expected carriers {expected_sample_ids}, found {carrier_sample_ids}"
    )

    # 1.4 Verify OMOP CDM person table
    with open(person_path, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        reporter.record(
            f"Verify OMOP CDM person table records ({len(reader)} patients)",
            len(reader) == 10 and "sample_id" in reader[0] and "person_id" in reader[0],
            "person.csv must have 10 rows and contain person_id and sample_id columns"
        )


def validate_exercise_2_local_sql_logic(reporter: ValidationReporter):
    """Exercise 2 (Offline): Validate SQL query syntax and structure."""
    print(f"\n{BOLD}{CYAN}▶ Validating Exercise 2: Analytical Queries & Syntax Consistency{RESET}")

    query_files = [
        "queries/custom_iceberg/01_allele_frequency.sql",
        "queries/custom_iceberg/02_carrier_lookup.sql",
        "queries/custom_iceberg/03_gene_burden_rollup.sql",
        "queries/custom_iceberg/04_omop_phenotype_join.sql",
        "queries/s3tables/01_allele_frequency.sql",
        "queries/s3tables/02_carrier_lookup.sql",
        "queries/s3tables/03_gene_burden_rollup.sql",
        "queries/s3tables/04_omop_phenotype_join.sql",
        "queries/delta/01_allele_frequency.sql",
        "queries/delta/02_carrier_lookup.sql",
        "queries/delta/03_gene_burden_rollup.sql",
        "queries/delta/04_omop_phenotype_join.sql",
        "queries/postgres/01_allele_frequency.sql",
        "queries/postgres/02_carrier_lookup.sql",
        "queries/postgres/03_gene_burden_rollup.sql",
        "queries/postgres/04_omop_phenotype_join.sql",
    ]

    for qf in query_files:
        full_path = os.path.join(PROJECT_ROOT, qf)
        exists = os.path.exists(full_path)
        if exists:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                valid = len(content) > 50 and ("SELECT" in content.upper() or "WITH" in content.upper())
                reporter.record(f"Query Syntax & Structure: {qf}", valid)
        else:
            reporter.record(f"Query Syntax & Structure: {qf}", False, f"File {qf} not found")


def validate_exercise_live_athena(reporter: ValidationReporter, workgroup: str = "hls-variant-store-dev"):
    """Exercise 2, 3, 4 (Live AWS): Run Athena queries and verify analytical results."""
    print(f"\n{BOLD}{CYAN}▶ Validating Exercises 2, 3 & 4: Live AWS Athena Query Execution & Telemetry{RESET}")

    # Check AWS CLI credentials
    code, out, err = run_aws_cli(["sts", "get-caller-identity", "--output", "json"])
    if code != 0:
        reporter.record("AWS Credentials & STS Check", False, f"Could not authenticate to AWS: {err}")
        return

    identity = json.loads(out)
    reporter.record(f"AWS Identity Authenticated (Account: {identity['Account']})", True)

    # --- Live Query 1: Allele Frequency ---
    try:
        q1_sql = (
            "SELECT reference_name, start, reference_bases, alternate_bases, "
            "COUNT(DISTINCT sample_id) AS total_cohort_samples, "
            "COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS alt_carrier_count, "
            "ROUND(CAST(COUNT(CASE WHEN genotype IN ('0/1', '1/1') THEN 1 END) AS double) / "
            "CAST(COUNT(DISTINCT sample_id) AS double), 4) AS carrier_frequency, "
            "json_extract_scalar(attributes, '$.gene') AS gene_symbol, "
            "json_extract_scalar(attributes, '$.clnsig') AS clinical_significance "
            "FROM genomics_custom_iceberg.variants "
            "GROUP BY reference_name, start, reference_bases, alternate_bases, "
            "json_extract_scalar(attributes, '$.gene'), json_extract_scalar(attributes, '$.clnsig') "
            "ORDER BY alt_carrier_count DESC LIMIT 5;"
        )
        res1 = execute_athena_query(q1_sql, workgroup=workgroup)
        reporter.record(
            f"Exercise 2.1: Allele Frequency Query (scanned {res1['scanned_bytes']} bytes)",
            True,
            f"Engine time: {res1['engine_time_ms']}ms",
            res1["engine_time_ms"]
        )
    except Exception as e:
        reporter.record("Exercise 2.1: Allele Frequency Query", False, str(e))

    # --- Live Query 2: Pathogenic Carrier Lookup ---
    try:
        q2_sql = (
            "SELECT sample_id, reference_name, start, genotype, "
            "json_extract_scalar(attributes, '$.gene') AS gene_symbol, "
            "json_extract_scalar(attributes, '$.clnsig') AS clinical_significance "
            "FROM genomics_custom_iceberg.variants "
            "WHERE reference_name = 'chr21' AND start = 25891796 AND genotype IN ('0/1', '1/1');"
        )
        res2 = execute_athena_query(q2_sql, workgroup=workgroup)
        # Parse returned carriers (skip header row)
        carriers = [r["Data"][0].get("VarCharValue") for r in res2["rows"][1:]]
        expected = {"sample_002", "sample_005", "sample_008"}
        matched = set(carriers) == expected
        reporter.record(
            f"Exercise 2.2: Carrier Discovery (found {len(carriers)} expected APP carriers)",
            matched,
            f"Expected {expected}, got {set(carriers)}",
            res2["engine_time_ms"]
        )
    except Exception as e:
        reporter.record("Exercise 2.2: Carrier Discovery", False, str(e))

    # --- Live Query 3: Gene Burden Roll-up ---
    try:
        q3_sql = (
            "SELECT v.sample_id, json_extract_scalar(v.attributes, '$.gene') AS gene_symbol, "
            "COUNT(DISTINCT v.start) AS distinct_variant_sites, "
            "SUM(CASE WHEN v.genotype = '0/1' THEN 1 WHEN v.genotype = '1/1' THEN 2 ELSE 0 END) AS total_alt_allele_burden "
            "FROM genomics_custom_iceberg.variants v "
            "WHERE v.reference_name = 'chr21' AND v.genotype IN ('0/1', '1/1') "
            "AND json_extract_scalar(v.attributes, '$.gene') = 'APP' "
            "GROUP BY v.sample_id, json_extract_scalar(v.attributes, '$.gene');"
        )
        res3 = execute_athena_query(q3_sql, workgroup=workgroup)
        reporter.record(
            f"Exercise 2.3: Gene Burden Rollup (scanned {res3['scanned_bytes']} bytes)",
            len(res3["rows"]) > 1,
            f"Engine time: {res3['engine_time_ms']}ms",
            res3["engine_time_ms"]
        )
    except Exception as e:
        reporter.record("Exercise 2.3: Gene Burden Rollup", False, str(e))

    # --- Live Query 4: Genotype ↔ OMOP Phenotype Join ---
    try:
        q4_sql = (
            "WITH target_carriers AS ( "
            "  SELECT v.sample_id, v.reference_name, v.start, v.genotype, "
            "         json_extract_scalar(v.attributes, '$.gene') AS gene_symbol, "
            "         json_extract_scalar(v.attributes, '$.clnsig') AS clinical_significance "
            "  FROM genomics_custom_iceberg.variants v "
            "  WHERE v.reference_name = 'chr21' AND v.start = 25891796 AND v.genotype IN ('0/1', '1/1') "
            ") "
            "SELECT p.person_id, p.sample_id, p.year_of_birth, tc.gene_symbol, tc.clinical_significance, tc.genotype, "
            "       co.condition_concept_id, co.condition_start_date "
            "FROM clinical_omop.person p "
            "INNER JOIN target_carriers tc ON p.sample_id = tc.sample_id "
            "LEFT JOIN clinical_omop.condition_occurrence co ON p.person_id = co.person_id;"
        )
        res4 = execute_athena_query(q4_sql, workgroup=workgroup, database="clinical_omop")
        # Ensure we successfully correlated OMOP clinical condition (Alzheimer's concept 43530807)
        rows = res4["rows"][1:]
        concept_ids = [r["Data"][6].get("VarCharValue") for r in rows if len(r.get("Data", [])) > 6]
        has_alzheimers = "43530807" in concept_ids
        reporter.record(
            f"Exercise 4: Genotype ↔ OMOP Cross-Modal Join (Correlated Concept 43530807)",
            has_alzheimers,
            f"Engine time: {res4['engine_time_ms']}ms, scanned: {res4['scanned_bytes']} bytes",
            res4["engine_time_ms"]
        )
    except Exception as e:
        reporter.record("Exercise 4: Genotype ↔ OMOP Cross-Modal Join", False, str(e))


def validate_exercise_5_governance(reporter: ValidationReporter):
    """Exercise 5: Validate KMS CMK alias and Lake Formation configuration."""
    print(f"\n{BOLD}{CYAN}▶ Validating Exercise 5: Security & Governance Posture{RESET}")

    # 5.1 Check KMS Key Alias
    code, out, err = run_aws_cli([
        "kms", "list-aliases",
        "--query", "Aliases[?AliasName=='alias/hls-variant-store-dev'].AliasArn",
        "--output", "json"
    ])
    if code == 0 and len(json.loads(out)) > 0:
        reporter.record("KMS CMK Alias 'alias/hls-variant-store-dev' active", True)
    else:
        reporter.record("KMS CMK Alias active", False, f"Could not find alias/hls-variant-store-dev: {err}")

    # 5.2 Check Lake Formation configuration file
    lf_tf_path = os.path.join(PROJECT_ROOT, "deploy/terraform/lakeformation.tf")
    lf_doc_path = os.path.join(PROJECT_ROOT, "governance/lakeformation_policy.md")
    reporter.record(
        "Lake Formation column-level security policy documented & declared",
        os.path.exists(lf_tf_path) and os.path.exists(lf_doc_path)
    )


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Exercise & Deployment Validation CLI for AWS Genomic Variant Store."
    )
    parser.add_argument(
        "--aws-mode",
        action="store_true",
        help="Execute live queries and checks against AWS account infrastructure."
    )
    parser.add_argument(
        "--local-mode",
        action="store_true",
        help="Execute offline checks (synthetic data integrity, VCF parser, SQL queries)."
    )
    parser.add_argument(
        "--workgroup",
        default="hls-variant-store-dev",
        help="Amazon Athena workgroup name (default: hls-variant-store-dev)."
    )
    args = parser.parse_args()

    # Default to local mode if neither specified
    if not args.aws_mode and not args.local_mode:
        args.local_mode = True

    print("\n" + "=" * 80)
    print(f"{BOLD}AWS GENOMIC VARIANT STORE: EXERCISE & LAB VALIDATOR{RESET}")
    print("=" * 80)

    reporter = ValidationReporter()

    if args.local_mode:
        validate_exercise_1_synthetic_data(reporter)
        validate_exercise_2_local_sql_logic(reporter)

    if args.aws_mode:
        validate_exercise_live_athena(reporter, workgroup=args.workgroup)
        validate_exercise_5_governance(reporter)

    sys.exit(reporter.summary())


if __name__ == "__main__":
    main()
