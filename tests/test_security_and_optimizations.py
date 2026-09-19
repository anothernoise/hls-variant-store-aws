"""
Unit tests for Top 16 Security and Optimization improvements:
- SQL injection defense & gene whitelisting
- Identifier sanitization
- S3 Tables dot-notation namespace
- Backend Singleton pattern
- Scaling trajectory memoization
- CORS origin hardening
"""

import unittest
from app.backend_modules.sql_builder import SqlBuilder
from app.backend_modules.base import VariantStoreBackend
from benchmarks.benchmark_runner import generate_cohort_scaling_curve, _SCALING_CURVE_CACHE
from api.main import app as fastapi_app


class TestSecurityAndOptimizations(unittest.TestCase):
    def test_sql_builder_whitelisted_genes(self):
        """Verify valid clinical genes generate dialect-specific queries."""
        config = {
            "database": "genomics_custom_iceberg",
            "table_name": "variants"
        }
        for gene in ["APP", "SOD1", "BRCA1"]:
            sql_carriers = SqlBuilder.build_engine_sql(config, "Custom S3 + Iceberg", query_kind="carriers", gene=gene)
            self.assertIn("SELECT", sql_carriers)
            self.assertIn("genomics_custom_iceberg.variants", sql_carriers)

            sql_burden = SqlBuilder.build_engine_sql(config, "Custom S3 + Iceberg", query_kind="burden", gene=gene)
            self.assertIn("SELECT", sql_burden)
            self.assertIn("SUM(", sql_burden)

    def test_sql_builder_injection_rejection(self):
        """Verify malicious SQL injection attempts into gene parameter are rejected with ValueError."""
        config = {
            "database": "genomics_custom_iceberg",
            "table_name": "variants"
        }
        malicious_inputs = [
            "APP' OR '1'='1",
            "APP; DROP TABLE variants; --",
            "SOD1' UNION SELECT * FROM users --",
            "<script>alert(1)</script>",
            "UNKNOWN_GENE"
        ]
        for bad_gene in malicious_inputs:
            with self.assertRaises(ValueError):
                SqlBuilder.build_engine_sql(config, "Custom S3 + Iceberg", query_kind="carriers", gene=bad_gene)

    def test_sanitize_identifier(self):
        """Verify schema/table identifier sanitizer prevents injection."""
        valid_id = SqlBuilder.sanitize_identifier("genomics_s3tables")
        self.assertEqual(valid_id, "genomics_s3tables")

        valid_dot_id = SqlBuilder.sanitize_identifier("s3tablescatalog.genomics")
        self.assertEqual(valid_dot_id, "s3tablescatalog.genomics")

        with self.assertRaises(ValueError):
            SqlBuilder.sanitize_identifier("genomics; DROP TABLE", strict=True)

        with self.assertRaises(ValueError):
            SqlBuilder.sanitize_identifier("genomics' OR '1'='1", strict=True)

    def test_s3_tables_dot_namespace(self):
        """Verify S3 Tables catalog uses dot-notation namespace formatting."""
        config = {
            "database": "s3tablescatalog.genomics",
            "table_name": "variants"
        }
        sql = SqlBuilder.build_engine_sql(config, "Amazon S3 Tables", query_kind="af")
        self.assertIn("s3tablescatalog.genomics.variants", sql)

    def test_backend_singleton_pattern(self):
        """Verify VariantStoreBackend adheres to Singleton pattern to avoid re-parsing data into RAM."""
        backend1 = VariantStoreBackend()
        backend2 = VariantStoreBackend()
        self.assertIs(backend1, backend2, "VariantStoreBackend must be a singleton instance")

    def test_scaling_curve_memoization(self):
        """Verify generate_cohort_scaling_curve memoizes results across calls."""
        _SCALING_CURVE_CACHE.clear()
        self.assertEqual(len(_SCALING_CURVE_CACHE), 0)

        curve1 = generate_cohort_scaling_curve()
        self.assertGreater(len(_SCALING_CURVE_CACHE), 0)
        self.assertGreater(len(curve1), 0)

        # Second call should retrieve from cache
        curve2 = generate_cohort_scaling_curve()
        self.assertEqual(curve1, curve2)

    def test_cors_middleware_configuration(self):
        """Verify FastAPI CORS middleware does not permit wildcard origins with credentials."""
        cors_middlewares = [m for m in fastapi_app.user_middleware if "CORSMiddleware" in str(m.cls)]
        self.assertGreater(len(cors_middlewares), 0)
        cors_options = cors_middlewares[0].kwargs
        allow_origins = cors_options.get("allow_origins", [])
        allow_credentials = cors_options.get("allow_credentials", False)

        if allow_credentials:
            self.assertNotIn("*", allow_origins, "Wildcard '*' must not be allowed when allow_credentials is True")


if __name__ == "__main__":
    unittest.main()
