"""
Unit tests for benchmark metrics, cost calculations, and custom Iceberg partitioning.
"""

import unittest
from benchmarks.benchmark_runner import calculate_athena_cost, simulate_query_metrics, run_n1_ingest_benchmark
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

    def test_simulate_query_metrics(self):
        res = simulate_query_metrics("S3 Tables", "allele_frequency", cohort_size=10)
        self.assertEqual(res["strategy"], "S3 Tables")
        self.assertEqual(res["query_type"], "allele_frequency")
        self.assertGreater(res["mb_scanned"], 10.0)
        self.assertGreater(res["execution_time_ms"], 0.0)
        self.assertGreater(res["cost_usd"], 0.0)

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
