"""
Unit tests for VariantStoreApiClient.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.api_client import VariantStoreApiClient


class TestVariantStoreApiClient(unittest.TestCase):
    def setUp(self):
        self.client = VariantStoreApiClient(base_url="http://mock-api:8000")

    @patch("requests.Session.get")
    def test_is_api_alive_success(self, mock_get):
        mock_get.return_value.status_code = 200
        self.assertTrue(self.client.is_api_alive())

    @patch("requests.Session.get")
    def test_is_api_alive_failure(self, mock_get):
        mock_get.side_effect = Exception("Connection error")
        self.assertFalse(self.client.is_api_alive())

    @patch("requests.Session.get")
    def test_get_allele_frequencies_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [{"reference_name": "chr21", "af": 0.4}],
            "telemetry": {"latency_ms": 25.0, "mode": "offline"}
        }
        mock_get.return_value = mock_resp

        df, tel = self.client.get_allele_frequencies("Amazon S3 Tables", offline=True)
        self.assertEqual(len(df), 1)
        self.assertEqual(tel["latency_ms"], 25.0)

    @patch("requests.Session.get")
    def test_fallback_when_api_fails(self, mock_get):
        mock_get.side_effect = Exception("Server down")
        df, tel = self.client.get_allele_frequencies("Amazon S3 Tables", offline=True)
        self.assertFalse(df.empty)
        self.assertEqual(tel["mode"], "offline")

    @patch("requests.Session.get")
    def test_get_carrier_lookup_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [{"sample_id": "NA12878", "gene_symbol": "APP"}],
            "telemetry": {"latency_ms": 18.0, "mode": "offline"}
        }
        mock_get.return_value = mock_resp

        df, tel = self.client.get_pathogenic_carriers("Custom S3 + Iceberg", gene="APP", offline=True)
        self.assertEqual(len(df), 1)

    @patch("requests.Session.get")
    def test_get_gene_burden_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [{"sample_id": "NA12878", "total_alt_allele_burden": 3}],
            "telemetry": {"latency_ms": 15.0, "mode": "offline"}
        }
        mock_get.return_value = mock_resp

        df, tel = self.client.get_gene_burden("Delta Lake on S3", offline=True)
        self.assertEqual(len(df), 1)

    @patch("requests.Session.get")
    def test_get_omop_phenotype_join_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [{"person_id": "P001", "condition_concept_id": "378419"}],
            "telemetry": {"latency_ms": 22.0, "mode": "offline"}
        }
        mock_get.return_value = mock_resp

        df, tel = self.client.get_omop_phenotype_join("Hail VDS (Spark)", offline=True)
        self.assertEqual(len(df), 1)

    @patch("requests.Session.get")
    def test_get_raw_store_data_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [{"sample_id": "sample_001", "start": 25891796}],
            "telemetry": {"latency_ms": 12.0, "mode": "offline"},
            "sql": "SELECT 1"
        }
        mock_get.return_value = mock_resp

        df, tel, sql = self.client.get_raw_store_data("Amazon S3 Tables", offline=True)
        self.assertEqual(len(df), 1)
        self.assertEqual(sql, "SELECT 1")

    @patch("requests.Session.get")
    def test_get_benchmarks_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"engine": "Amazon S3 Tables", "cost_per_query": "$0.000063"}]
        mock_get.return_value = mock_resp

        benchmarks = self.client.get_benchmarks()
        self.assertEqual(len(benchmarks), 1)

    @patch("requests.Session.post")
    def test_feed_engine_from_api(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {
            "batch_id": "batch_abc123",
            "engine": "s3_tables",
            "records_ingested": 1,
            "duration_ms": 15.0,
            "status": "COMPLETED",
            "target_table": "s3tablescatalog.variants"
        }
        mock_post.return_value = mock_resp

        res = self.client.feed_engine(
            engine="s3_tables",
            records=[{"reference_name": "chr1", "start": 100}],
            cohort_id="c1"
        )
        self.assertEqual(res["records_ingested"], 1)
        self.assertEqual(res["engine"], "s3_tables")

    @patch("requests.Session.post")
    def test_feed_engine_fallback(self, mock_post):
        mock_post.side_effect = Exception("API connection dropped")
        res = self.client.feed_engine(
            engine="Amazon S3 Tables",
            records=[{"reference_name": "chr1", "start": 100, "sample_id": "s1", "genotype": "0/1"}],
            cohort_id="c1"
        )
        self.assertEqual(res["records_ingested"], 1)
        self.assertEqual(res["status"], "COMPLETED")

    @patch("requests.Session.get")
    def test_get_engine_health_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "engine_id": "s3_tables",
            "status": "pass",
            "deployment_status": "ACTIVE",
            "checks": {},
            "latency_ms": 1.2
        }
        mock_get.return_value = mock_resp

        data = self.client.get_engine_health("s3_tables")
        self.assertEqual(data["engine_id"], "s3_tables")
        self.assertEqual(data["status"], "pass")

    @patch("requests.Session.get")
    def test_get_all_engines_health_from_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "healthy",
            "total_engines": 7,
            "engines": {}
        }
        mock_get.return_value = mock_resp

        data = self.client.get_all_engines_health()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["total_engines"], 7)

    @patch("requests.Session.post")
    def test_run_benchmarks_from_api(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "mode": "simulated",
            "cohort_size": 100,
            "engine_summary": [{"engine": "Amazon S3 Tables", "cost_per_query": "$0.000141"}],
            "ai_analysis": {"recommendation": "Top performer: Amazon S3 Tables"}
        }
        mock_post.return_value = mock_resp

        res = self.client.run_benchmarks(mode="simulated", cohort_size=100)
        self.assertEqual(res["mode"], "simulated")
        self.assertEqual(res["cohort_size"], 100)
        self.assertIn("ai_analysis", res)

    @patch("requests.Session.post")
    def test_run_benchmarks_fallback_on_api_error(self, mock_post):
        mock_post.side_effect = Exception("FastAPI unreachable")
        res = self.client.run_benchmarks(mode="simulated", cohort_size=50)
        self.assertEqual(res["mode"], "simulated")
        self.assertEqual(res["cohort_size"], 50)
        self.assertIn("engine_summary", res)
        self.assertIn("ai_analysis", res)


if __name__ == "__main__":
    unittest.main()


