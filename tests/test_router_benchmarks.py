"""
Unit tests for FastAPI Benchmarks router endpoints:
GET /api/v1/benchmarks
POST /api/v1/benchmarks/run
"""

import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestBenchmarksRouter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_benchmarks(self):
        resp = self.client.get("/api/v1/benchmarks")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("engine", data[0])
        self.assertIn("cost_per_query", data[0])

    def test_post_run_benchmarks_simulated(self):
        payload = {
            "mode": "simulated",
            "cohort_size": 25,
            "engines": ["Amazon S3 Tables", "Delta Lake on S3"]
        }
        resp = self.client.post("/api/v1/benchmarks/run", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["mode"], "simulated")
        self.assertEqual(data["cohort_size"], 25)
        self.assertIn("engine_summary", data)
        self.assertIn("ai_analysis", data)
        self.assertIn("recommendation", data["ai_analysis"])
        self.assertIn("top_engine", data["ai_analysis"])

    def test_post_run_benchmarks_invalid_cohort(self):
        payload = {
            "mode": "simulated",
            "cohort_size": 0
        }
        resp = self.client.post("/api/v1/benchmarks/run", json=payload)
        self.assertEqual(resp.status_code, 422)  # Validation error
