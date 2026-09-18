"""
Unit tests for the FastAPI Middle Layer.
Tests REST API endpoints for engine management, query execution, and benchmarks in both online and offline modes.
"""

import unittest
from fastapi.testclient import TestClient

try:
    from api.main import app
except ImportError:
    app = None


class TestFastAPIMiddleLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if app is None:
            raise unittest.SkipTest("FastAPI app not yet implemented")
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("version", data)

    def test_list_engines(self):
        response = self.client.get("/api/v1/engines")
        self.assertEqual(response.status_code, 200)
        engines = response.json()
        self.assertIsInstance(engines, list)
        self.assertGreaterEqual(len(engines), 7)
        engine_ids = [e["id"] for e in engines]
        self.assertIn("s3_tables", engine_ids)
        self.assertIn("custom_iceberg", engine_ids)
        self.assertIn("delta_lake", engine_ids)

    def test_get_engine_by_id(self):
        response = self.client.get("/api/v1/engines/s3_tables")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "s3_tables")
        self.assertEqual(data["name"], "Amazon S3 Tables")
        self.assertIn("architecture", data)

    def test_get_unknown_engine_returns_404(self):
        response = self.client.get("/api/v1/engines/unknown_engine_xyz")
        self.assertEqual(response.status_code, 404)

    def test_allele_frequencies_offline(self):
        response = self.client.get("/api/v1/engines/s3_tables/allele-frequencies?offline=true")
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertIn("records", res)
        self.assertIn("telemetry", res)
        self.assertEqual(res["telemetry"]["mode"], "offline")
        self.assertGreater(len(res["records"]), 0)

    def test_carrier_lookup_offline(self):
        response = self.client.get("/api/v1/engines/custom_iceberg/carrier-lookup?offline=true&gene=APP")
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertEqual(res["telemetry"]["mode"], "offline")
        self.assertGreater(len(res["records"]), 0)
        first = res["records"][0]
        self.assertEqual(first.get("gene_symbol"), "APP")

    def test_gene_burden_offline(self):
        response = self.client.get("/api/v1/engines/delta_lake/gene-burden?offline=true")
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertEqual(res["telemetry"]["mode"], "offline")
        self.assertGreater(len(res["records"]), 0)

    def test_omop_phenotype_join_offline(self):
        response = self.client.get("/api/v1/engines/hail_vds/omop-phenotype-join?offline=true")
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertEqual(res["telemetry"]["mode"], "offline")
        self.assertGreater(len(res["records"]), 0)

    def test_raw_records_offline(self):
        response = self.client.get("/api/v1/engines/s3_tables/raw-records?offline=true&table_name=variants&limit=5")
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertIn("sql", res)
        self.assertLessEqual(len(res["records"]), 5)

    def test_benchmarks_endpoint(self):
        response = self.client.get("/api/v1/benchmarks")
        self.assertEqual(response.status_code, 200)
        benchmarks = response.json()
        self.assertIsInstance(benchmarks, list)
    def test_feed_engine_batch(self):
        payload = {
            "cohort_id": "test_online_cohort",
            "records": [
                {
                    "reference_name": "chr17",
                    "start": 43044295,
                    "end": 43044295,
                    "reference_bases": "A",
                    "alternate_bases": "G",
                    "sample_id": "sample_001",
                    "genotype": "0/1",
                    "dp": 40,
                    "gq": 99,
                    "allele_depth": "20,20",
                    "attributes": "{\"gene\": \"BRCA1\", \"clnsig\": \"PATHOGENIC\"}"
                }
            ]
        }
        response = self.client.post("/api/v1/engines/s3_tables/feed", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["records_ingested"], 1)
        self.assertEqual(data["engine"], "s3_tables")
        self.assertEqual(data["status"], "COMPLETED")

    def test_feed_unknown_engine_returns_404(self):
        payload = {"cohort_id": "c1", "records": []}
        response = self.client.post("/api/v1/engines/invalid_engine_xyz/feed", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_engine_health_success(self):
        response = self.client.get("/api/v1/engines/s3_tables/health?offline=true")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["engine_id"], "s3_tables")
        self.assertEqual(data["status"], "pass")
        self.assertEqual(data["deployment_status"], "ACTIVE")
        self.assertIn("checks", data)
        self.assertIn("timestamp", data)

    def test_engine_health_unknown_engine_404(self):
        response = self.client.get("/api/v1/engines/nonexistent_xyz/health")
        self.assertEqual(response.status_code, 404)

    def test_rds_postgres_active_health(self):
        response = self.client.get("/api/v1/engines/rds_postgres/health?offline=true")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "pass")
        self.assertEqual(data["deployment_status"], "ACTIVE")

    def test_all_engines_health_summary(self):
        response = self.client.get("/api/v1/engines/health/all?offline=true")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertGreaterEqual(data["total_engines"], 4)
        self.assertIn("engines", data)


if __name__ == "__main__":
    unittest.main()

