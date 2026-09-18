"""
Unit tests for VariantStoreBackend and JSON metadata integration.
Adheres to TDD principles and verifies >= 80% coverage on app/backend.py.
"""

import os
import json
import unittest
from app.backend import VariantStoreBackend, PROJECT_ROOT

REQUIRED_ARCH_KEYS = [
    "Engine Class",
    "Table Format",
    "Catalog Integration",
    "Physical Location",
    "Partitioning Scheme",
    "Compression / Format",
    "Compaction Maintenance",
    "Security & Governance"
]

EXPECTED_ENGINES = [
    "Amazon S3 Tables",
    "Custom S3 + Iceberg",
    "Delta Lake on S3",
    "Hail VDS (Spark)",
    "Amazon Aurora PostgreSQL (Serverless v2)",
    "Amazon RDS PostgreSQL",
    "AWS HealthOmics Variant Store"
]


class TestBackendMetadata(unittest.TestCase):
    def setUp(self):
        self.backend = VariantStoreBackend()
        self.metadata_dir = os.path.join(PROJECT_ROOT, "app", "metadata")

    def test_metadata_directory_exists(self):
        self.assertTrue(
            os.path.isdir(self.metadata_dir),
            f"Metadata directory does not exist: {self.metadata_dir}"
        )

    def test_all_expected_engines_have_json_files(self):
        json_files = [f for f in os.listdir(self.metadata_dir) if f.endswith(".json")]
        self.assertGreaterEqual(len(json_files), 7, "At least 7 engine JSON files required")

    def test_engine_json_schema(self):
        for fname in os.listdir(self.metadata_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self.metadata_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("id", data, f"Missing 'id' in {fname}")
            self.assertIn("name", data, f"Missing 'name' in {fname}")
            self.assertIn("database", data, f"Missing 'database' in {fname}")
            self.assertIn("table_name", data, f"Missing 'table_name' in {fname}")
            self.assertIn("architecture", data, f"Missing 'architecture' in {fname}")
            
            arch = data["architecture"]
            for key in REQUIRED_ARCH_KEYS:
                self.assertIn(key, arch, f"Missing architecture key '{key}' in {fname}")
                self.assertTrue(isinstance(arch[key], str), f"Architecture key '{key}' must be str")

    def test_supported_engines_list(self):
        self.assertEqual(len(self.backend.SUPPORTED_ENGINES), len(EXPECTED_ENGINES))
        for exp in EXPECTED_ENGINES:
            self.assertIn(exp, self.backend.SUPPORTED_ENGINES)

    def test_get_store_metadata_for_each_engine(self):
        for engine in EXPECTED_ENGINES:
            meta = self.backend.get_store_metadata(engine)
            self.assertIsInstance(meta, dict)
            for key in REQUIRED_ARCH_KEYS:
                self.assertIn(key, meta, f"Missing '{key}' for engine '{engine}'")

    def test_get_store_metadata_fallback(self):
        meta = self.backend.get_store_metadata("NonExistentEngine")
        self.assertIsInstance(meta, dict)
        for key in REQUIRED_ARCH_KEYS:
            self.assertIn(key, meta)

    def test_get_engine_config(self):
        config = self.backend.get_engine_config("Amazon S3 Tables")
        self.assertEqual(config["name"], "Amazon S3 Tables")
        self.assertEqual(config["database"], "s3tablescatalog/genomics")
        self.assertIn("architecture", config)

    def test_get_raw_store_data_variants(self):
        df, telemetry, sql = self.backend.get_raw_store_data(
            engine="Custom S3 + Iceberg",
            table_name="variants",
            chromosome="chr21",
            limit=10
        )
        self.assertIn("Custom S3 + Iceberg", telemetry["engine"])
        self.assertIn("variants", telemetry["table"])
        self.assertIn("SELECT", sql)
        self.assertIn("chr21", sql)

    def test_get_raw_store_data_person(self):
        df, telemetry, sql = self.backend.get_raw_store_data(
            engine="Amazon S3 Tables",
            table_name="person",
            limit=5
        )
        self.assertIn("person", telemetry["table"])
        self.assertIn("SELECT", sql)

    def test_get_allele_frequencies(self):
        df, telemetry = self.backend.get_allele_frequencies("Amazon S3 Tables")
        self.assertFalse(df.empty)
        self.assertIn("latency_ms", telemetry)
        self.assertIn("scanned_bytes", telemetry)

    def test_get_pathogenic_carriers(self):
        df, telemetry = self.backend.get_pathogenic_carriers(
            engine="Custom S3 + Iceberg",
            gene="APP"
        )
        self.assertFalse(df.empty)
        self.assertIn("latency_ms", telemetry)

    def test_get_gene_burden(self):
        df, telemetry = self.backend.get_gene_burden("Amazon S3 Tables")
        self.assertFalse(df.empty)
        self.assertIn("latency_ms", telemetry)

    def test_get_omop_phenotype_join(self):
        df, telemetry = self.backend.get_omop_phenotype_join("Amazon S3 Tables")
        self.assertFalse(df.empty)
        self.assertIn("query_type", telemetry)

    def test_fallback_dataframe_generation(self):
        df_af = self.backend._get_fallback_dataframe("allele_frequency")
        self.assertFalse(df_af.empty)
        df_car = self.backend._get_fallback_dataframe("carriers")
        self.assertFalse(df_car.empty)
        df_omop = self.backend._get_fallback_dataframe("omop")
        self.assertFalse(df_omop.empty)

    def test_offline_mode_attribute(self):
        self.assertFalse(self.backend.offline_mode)
        self.backend.offline_mode = True
        self.assertTrue(self.backend.offline_mode)
        self.backend.offline_mode = False

    def test_run_athena_sql_offline(self):
        df, lat, scanned, mode = self.backend.run_athena_sql("SELECT 1", offline=True)
        self.assertFalse(df.empty)
        self.assertEqual(mode, "offline")
        self.assertLess(lat, 50.0)

    def test_get_allele_frequencies_offline(self):
        df, telemetry = self.backend.get_allele_frequencies("Amazon S3 Tables", offline=True)
        self.assertFalse(df.empty)
        self.assertEqual(telemetry["mode"], "offline")

    def test_get_pathogenic_carriers_offline(self):
        df, telemetry = self.backend.get_pathogenic_carriers("Custom S3 + Iceberg", offline=True)
        self.assertFalse(df.empty)
        self.assertEqual(telemetry["mode"], "offline")

    def test_get_gene_burden_offline(self):
        df, telemetry = self.backend.get_gene_burden("Amazon S3 Tables", offline=True)
        self.assertFalse(df.empty)
        self.assertEqual(telemetry["mode"], "offline")

    def test_get_omop_phenotype_join_offline(self):
        df, telemetry = self.backend.get_omop_phenotype_join("Amazon S3 Tables", offline=True)
        self.assertFalse(df.empty)
        self.assertEqual(telemetry["mode"], "offline")

    def test_get_raw_store_data_offline(self):
        df_s3, telemetry, sql = self.backend.get_raw_store_data("Amazon S3 Tables", offline=True)
        self.assertFalse(df_s3.empty)
        self.assertEqual(telemetry["mode"], "offline")
        self.assertEqual(df_s3["engine"].iloc[0], "mock_data")
        self.assertIn("mock_data", telemetry["table"])

        df_delta, tel_delta, _ = self.backend.get_raw_store_data("Delta Lake on S3", offline=True)
        self.assertFalse(df_delta.empty)
        self.assertEqual(df_delta["engine"].iloc[0], "mock_data")

        df_hail, _, _ = self.backend.get_raw_store_data("Hail VDS (Spark)", offline=True)
        self.assertFalse(df_hail.empty)
        self.assertEqual(df_hail["engine"].iloc[0], "mock_data")

    def test_engine_query_sql_generation_s3_tables(self):
        sql = self.backend.build_engine_sql("Amazon S3 Tables", query_kind="af")
        self.assertTrue("s3tablescatalog" in sql or "genomics" in sql)

    def test_engine_query_sql_generation_delta_lake(self):
        sql = self.backend.build_engine_sql("Delta Lake on S3", query_kind="af")
        self.assertIn("genomics_delta.variants", sql)

    def test_engine_query_sql_generation_hail_vds(self):
        sql = self.backend.build_engine_sql("Hail VDS (Spark)", query_kind="af")
        self.assertIn("genomics_hail_vds.variant_data", sql)

    def test_engine_query_sql_generation_healthomics(self):
        sql = self.backend.build_engine_sql("AWS HealthOmics Variant Store", query_kind="af")
        self.assertIn("genomics_healthomics.variants", sql)

    def test_engine_query_sql_generation_postgres(self):
        sql = self.backend.build_engine_sql("Amazon Aurora PostgreSQL (Serverless v2)", query_kind="af")
        self.assertIn("attributes->>'gene'", sql)

    def test_engine_column_in_sql(self):
        sql = self.backend.build_engine_sql("Custom S3 + Iceberg", query_kind="carriers")
        self.assertIn("engine", sql)

    def test_feed_engine(self):
        res = self.backend.feed_engine(
            engine="Amazon S3 Tables",
            records=[
                {
                    "reference_name": "chr17",
                    "start": 43044295,
                    "end": 43044295,
                    "reference_bases": "A",
                    "alternate_bases": "G",
                    "sample_id": "sample_001",
                    "genotype": "0/1",
                    "attributes": "{\"gene\": \"BRCA1\"}"
                }
            ],
            cohort_id="cohort_test"
        )
        self.assertEqual(res["records_ingested"], 1)
        self.assertEqual(res["engine"], "s3_tables")
        self.assertEqual(res["status"], "COMPLETED")

    def test_check_engine_health_s3_tables(self):
        health = self.backend.check_engine_health("Amazon S3 Tables", offline=True)
        self.assertEqual(health["engine_id"], "s3_tables")
        self.assertEqual(health["status"], "pass")
        self.assertEqual(health["deployment_status"], "ACTIVE")
        self.assertIn("checks", health)

    def test_check_engine_health_rds_not_deployed(self):
        health = self.backend.check_engine_health("Amazon RDS PostgreSQL", offline=True)
        self.assertEqual(health["engine_id"], "rds_postgres")
        self.assertEqual(health["status"], "warn")
        self.assertEqual(health["deployment_status"], "NOT_DEPLOYED")

    def test_check_all_engines_health(self):
        summary = self.backend.check_all_engines_health(offline=True)
        self.assertIn("status", summary)
        self.assertGreaterEqual(summary["total_engines"], 7)
        self.assertIn("s3_tables", summary["engines"])


if __name__ == "__main__":
    unittest.main()


