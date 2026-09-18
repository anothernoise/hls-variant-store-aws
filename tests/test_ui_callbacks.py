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


if __name__ == "__main__":
    unittest.main()
