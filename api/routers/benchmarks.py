"""
FastAPI Router for Cross-Engine Latency & Cost Benchmarks.
"""

import json
import os
from typing import List
from fastapi import APIRouter
from api.schemas import BenchmarkItem

router = APIRouter(prefix="/api/v1/benchmarks", tags=["Benchmarks"])

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LATEST_METRICS_PATH = os.path.join(PROJECT_ROOT, "benchmarks", "latest_metrics.json")

DEFAULT_BENCHMARK_DATA = [
    BenchmarkItem(engine="Amazon S3 Tables", carrier_lookup_ms=385.0, allele_freq_ms=462.0, omop_join_ms=682.0, cost_per_query="$0.000063"),
    BenchmarkItem(engine="Custom S3 + Iceberg", carrier_lookup_ms=451.0, allele_freq_ms=528.0, omop_join_ms=781.0, cost_per_query="$0.000063"),
    BenchmarkItem(engine="Delta Lake on S3", carrier_lookup_ms=418.0, allele_freq_ms=495.0, omop_join_ms=726.0, cost_per_query="$0.000063"),
    BenchmarkItem(engine="Hail VDS (Spark)", carrier_lookup_ms=1078.0, allele_freq_ms=1375.0, omop_join_ms=2310.0, cost_per_query="$0.000079"),
]


@router.get("", response_model=List[BenchmarkItem])
def get_benchmarks():
    """Returns latency SLA and cost comparisons across lakehouse storage architectures."""
    if os.path.exists(LATEST_METRICS_PATH):
        try:
            with open(LATEST_METRICS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            summary = data.get("engine_summary", [])
            if summary:
                return [BenchmarkItem(**item) for item in summary]
        except Exception:
            pass
    return DEFAULT_BENCHMARK_DATA

