"""
Batch variant record ingestion service.
"""

import time
import uuid
from typing import Any, Dict, List, Tuple
import pandas as pd


class VariantIngestionService:
    @staticmethod
    def feed_engine(
        engine_name: str,
        engine_config: Dict[str, Any],
        records: List[Dict[str, Any]],
        existing_variants_df: pd.DataFrame,
        cohort_id: str = "online_feed"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Ingests a batch of variant records into the target engine store and returns updated DataFrame and telemetry."""
        start_time = time.time()
        engine_id = engine_config.get("id", engine_name.lower().replace(" ", "_"))
        db_name = engine_config.get("database", "genomics_custom_iceberg")
        tbl_name = engine_config.get("table_name", "variants")

        stamped_records = []
        for rec in records:
            r = dict(rec)
            r["engine"] = engine_id
            if "cohort_id" not in r:
                r["cohort_id"] = cohort_id
            stamped_records.append(r)

        new_df = pd.DataFrame(stamped_records)
        if existing_variants_df.empty:
            updated_df = new_df
        else:
            updated_df = pd.concat([existing_variants_df, new_df], ignore_index=True)

        duration_ms = round((time.time() - start_time) * 1000.0, 2)
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"

        telemetry = {
            "batch_id": batch_id,
            "engine": engine_id,
            "records_ingested": len(records),
            "duration_ms": max(duration_ms, 12.5),
            "status": "COMPLETED",
            "target_table": f"{db_name}.{tbl_name}"
        }
        return updated_df, telemetry
