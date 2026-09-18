"""
Unit tests for Dash UI callbacks including Refresh Data triggers and formatting.
"""

import unittest
import dash_bootstrap_components as dbc
from app.app import (
    render_tab_content,
    update_mode_status_badge,
    update_refresh_timestamp
)


class TestUICallbacks(unittest.TestCase):
    def test_update_refresh_timestamp_initial(self):
        result = update_refresh_timestamp(0)
        self.assertIn("bi-clock-history", str(result))
        self.assertIn("Initial Load", str(result))

    def test_update_refresh_timestamp_clicked(self):
        result = update_refresh_timestamp(3)
        self.assertIn("bi-check2-circle", str(result))
        self.assertIn("Refreshed", str(result))
        self.assertIn("UTC", str(result))

    def test_render_tab_content_with_refresh_clicks_offline(self):
        card = render_tab_content(
            active_tab="tab-af",
            engine="Amazon S3 Tables",
            is_online=False,
            refresh_clicks=2
        )
        self.assertIsInstance(card, dbc.Card)
        # Check that table contains records
        body = card.children[1]
        dt = body.children[2]
        self.assertGreater(len(dt.data), 0)
        self.assertEqual(dt.data[0]["engine"], "mock_data")

    def test_render_tab_content_health_tab_refresh(self):
        card = render_tab_content(
            active_tab="tab-health",
            engine="Amazon S3 Tables",
            is_online=False,
            refresh_clicks=1
        )
        self.assertIsInstance(card, dbc.Card)

    def test_render_tab_content_rds_postgres(self):
        card = render_tab_content(
            active_tab="tab-af",
            engine="Amazon RDS PostgreSQL",
            is_online=False,
            refresh_clicks=1
        )
        self.assertIsInstance(card, dbc.Card)
        body = card.children[1]
        dt = body.children[2]
        self.assertGreater(len(dt.data), 0)

    def test_update_telemetry_badge_lakehouse(self):
        from app.app import update_telemetry_badge
        badge_card = update_telemetry_badge("Amazon S3 Tables", is_online=False, refresh_clicks=1)
        self.assertIsInstance(badge_card, dbc.Card)
        self.assertIn("Health: ACTIVE", str(badge_card))

    def test_update_engine_dropdown_options(self):
        from app.app import update_engine_dropdown_options
        options, value = update_engine_dropdown_options(is_online=False, refresh_clicks=0, current_value="Amazon S3 Tables")
        self.assertGreaterEqual(len(options), 4)
        labels = [o["label"] for o in options]
        self.assertIn("Amazon S3 Tables", labels)
        self.assertIn("Custom S3 + Iceberg", labels)
        self.assertIn("Delta Lake on S3", labels)
        self.assertIn("Hail VDS (Spark)", labels)
    def test_render_tab_content_benchmarks_tab(self):
        card = render_tab_content(
            active_tab="tab-benchmarks",
            engine="Amazon S3 Tables",
            is_online=False,
            refresh_clicks=0
        )
        self.assertIsInstance(card, dbc.Card)
        self.assertIn("Multi-Engine Query Latency", str(card))
        self.assertIn("Run Perf Test", str(card))

    def test_handle_run_benchmark(self):
        from app.app import handle_run_benchmark
        result, status_badge = handle_run_benchmark(n_clicks=1, cohort_size=50, mode="simulated")
        self.assertIsNotNone(result)
        self.assertIn("AI Architectural Reasoning", str(result))
        self.assertIn("50 Samples", str(result))
        self.assertIn("50 samples", str(status_badge))

    def test_handle_run_benchmark_reactive_cohort_change(self):
        from app.app import handle_run_benchmark
        # Changing cohort dropdown without clicking button
        result, status_badge = handle_run_benchmark(n_clicks=None, cohort_size=250, mode="simulated")
        self.assertIsNotNone(result)
        self.assertIn("250 Samples", str(result))
        self.assertIn("Scaling Trajectory", str(result))
        self.assertIn("250 samples", str(status_badge))

    def test_update_cohort_dataset_context_offline(self):
        from app.app import update_cohort_dataset_context
        context_list = update_cohort_dataset_context(
            engine="Amazon S3 Tables",
            is_online=False,
            active_tab="tab-af",
            refresh_clicks=0
        )
        self.assertIsInstance(context_list, dbc.ListGroup)
        context_str = str(context_list)
        self.assertIn("Synthetic Simulation (Local Air-gap)", context_str)
        self.assertIn("Amazon S3 Tables (Mock Simulation)", context_str)
        self.assertIn("Allele Frequency", context_str)

    def test_update_cohort_dataset_context_online_and_tabs(self):
        from app.app import update_cohort_dataset_context
        # Tab OMOP online
        context_list = update_cohort_dataset_context(
            engine="Delta Lake on S3",
            is_online=True,
            active_tab="tab-omop",
            refresh_clicks=1
        )
        context_str = str(context_list)
        self.assertIn("Live AWS Lakehouse (us-east-1)", context_str)
        self.assertIn("Delta Lake on S3 (Cloud)", context_str)
    def test_benchmarks_loading_wrapper_has_stage_progress_indicator(self):
        from app.views.tab_benchmarks import render_benchmarks_tab
        card = render_benchmarks_tab()
        self.assertIsInstance(card, dbc.Card)
        card_str = str(card)
        self.assertIn("benchmarks-loading-wrapper", card_str)
        self.assertIn("Running Multi-Engine Performance Benchmarks", card_str)
        self.assertIn("Stage: Partition Pruning & Locus Seeks", card_str)

    def test_handle_run_benchmark_live_fast_failover(self):
        from app.app import handle_run_benchmark
        # Mode live with unprovisioned tables should complete quickly via fast probe
        result, status_badge = handle_run_benchmark(n_clicks=1, cohort_size=10, mode="live")
        self.assertIsNotNone(result)
        self.assertIn("10 Samples", str(result))
        self.assertIn("live", str(status_badge))


if __name__ == "__main__":
    unittest.main()

