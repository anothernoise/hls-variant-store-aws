"""
Unit tests for benchmark metrics, cost calculations, custom Iceberg partitioning,
and benchmark runner execution modes.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from benchmarks.benchmark_runner import (
    calculate_athena_cost,
    simulate_query_metrics,
    run_n1_ingest_benchmark,
    build_engine_summary,
    run_benchmark_suite,
    run_live_athena_query,
    LAKEHOUSE_STRATEGIES
)
from ingest.custom_iceberg.load_variants_custom import partition_records_by_chrom

class TestBenchmarkSuite(unittest.TestCase):
    def test_calculate_athena_cost_minimum_billable(self):
        # Queries scanning less than 10MB are billed at 10MB minimum
        cost_5mb = calculate_athena_cost(5 * 1024 * 1024)
        cost_10mb = calculate_athena_cost(10 * 1024 * 1024)
        self.assertEqual(cost_5mb, cost_10mb)
        self.assertAlmostEqual(cost_10mb, (10 * 1024 * 1024 / (1024 ** 4)) * 5.00, places=7)

    def test_calculate_athena_cost_large_scan(self):
        # 1 TB query should cost exactly $5.00
        cost_1tb = calculate_athena_cost(1024 ** 4)
        self.assertAlmostEqual(cost_1tb, 5.00, places=4)

    def test_simulate_query_metrics_lakehouse_engines(self):
        for strategy in LAKEHOUSE_STRATEGIES:
            res = simulate_query_metrics(strategy, "allele_frequency", cohort_size=20)
            self.assertEqual(res["strategy"], strategy)
            self.assertEqual(res["query_type"], "allele_frequency")
            self.assertGreater(res["mb_scanned"], 10.0)
            self.assertGreater(res["execution_time_ms"], 0.0)
            self.assertGreater(res["cost_usd"], 0.0)

    def test_build_engine_summary(self):
        query_results = [
            {"strategy": "Amazon S3 Tables", "query_type": "carrier_lookup", "execution_time_ms": 350.0, "cost_usd": 0.000063},
            {"strategy": "Amazon S3 Tables", "query_type": "allele_frequency", "execution_time_ms": 420.0, "cost_usd": 0.000063},
            {"strategy": "Amazon S3 Tables", "query_type": "omop_join", "execution_time_ms": 620.0, "cost_usd": 0.000063},
            {"strategy": "Amazon S3 Tables", "query_type": "gene_burden", "execution_time_ms": 490.0, "cost_usd": 0.000063},
        ]
        summary = build_engine_summary(query_results)
        self.assertEqual(len(summary), 1)
        item = summary[0]
        self.assertEqual(item["engine"], "Amazon S3 Tables")
        self.assertEqual(item["carrier_lookup_ms"], 350.0)
        self.assertEqual(item["allele_freq_ms"], 420.0)
        self.assertEqual(item["omop_join_ms"], 620.0)
        self.assertTrue(item["cost_per_query"].startswith("$"))

    def test_run_benchmark_suite_simulated(self):
        result = run_benchmark_suite(mode="simulated", cohort_size=10, strategies=LAKEHOUSE_STRATEGIES)
        self.assertEqual(result["mode"], "simulated")
        self.assertEqual(result["cohort_size"], 10)
        self.assertIn("query_benchmarks", result)
        self.assertIn("engine_summary", result)
        self.assertIn("n1_benchmarks", result)
        self.assertEqual(len(result["engine_summary"]), 4)

    @patch("benchmarks.benchmark_runner.subprocess.run")
    def test_run_live_athena_query_success(self, mock_run):
        # Mock Athena start-query-execution and get-query-execution
        mock_start = MagicMock(returncode=0, stdout='{"QueryExecutionId": "test-qid-123"}')
        mock_stat = MagicMock(returncode=0, stdout='''{
            "QueryExecution": {
                "Status": {"State": "SUCCEEDED"},
                "Statistics": {
                    "EngineExecutionTimeInMillis": 412,
                    "DataScannedInBytes": 15728640
                }
            }
        }''')
        mock_run.side_effect = [mock_start, mock_stat]

        res = run_live_athena_query(
            strategy="Custom S3 + Iceberg",
            query_type="allele_frequency",
            sql="SELECT * FROM variants LIMIT 10",
            database="genomics_custom_iceberg",
            workgroup="hls-variant-store-dev"
        )
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["execution_time_ms"], 412.0)
        self.assertEqual(res["bytes_scanned"], 15728640)
        self.assertGreater(res["cost_usd"], 0)

    @patch("benchmarks.benchmark_runner.subprocess.run")
    def test_run_live_athena_query_failure_fallback(self, mock_run):
        mock_run.side_effect = Exception("AWS Athena timeout or unreachable")
        res = run_live_athena_query(
            strategy="Custom S3 + Iceberg",
            query_type="allele_frequency",
            sql="SELECT * FROM variants LIMIT 10",
            database="genomics_custom_iceberg",
            workgroup="hls-variant-store-dev"
        )
        self.assertEqual(res["status"], "ERROR")
        self.assertIn("fallback_simulated", res)

    def test_n1_benchmark_speedup(self):
        res = run_n1_ingest_benchmark(batch1_size=5, batch2_size=5)
        self.assertGreater(res["speedup_factor"], 1.0)
        self.assertEqual(res["incremental_files_created"], 2)
        self.assertEqual(res["rewritten_files_full_recompute"], 4)

    def test_custom_partitioning(self):
        sample_records = [
            {"reference_name": "chr21", "start": 100, "sample_id": "s1"},
            {"reference_name": "chr21", "start": 200, "sample_id": "s2"},
            {"reference_name": "chr22", "start": 300, "sample_id": "s1"},
        ]
        partitions = partition_records_by_chrom(sample_records)
        self.assertIn("chr21", partitions)
        self.assertIn("chr22", partitions)
        self.assertEqual(len(partitions["chr21"]), 2)
        self.assertEqual(len(partitions["chr22"]), 1)

if __name__ == "__main__":
    unittest.main()

