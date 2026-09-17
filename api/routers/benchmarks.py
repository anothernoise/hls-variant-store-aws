"""
FastAPI Router for Cross-Engine Latency & Cost Benchmarks.
"""

from typing import List
from fastapi import APIRouter
from api.schemas import BenchmarkItem

router = APIRouter(prefix="/api/v1/benchmarks", tags=["Benchmarks"])

BENCHMARK_DATA = [
    BenchmarkItem(engine="Amazon S3 Tables", carrier_lookup_ms=385.0, allele_freq_ms=462.0, omop_join_ms=682.0, cost_per_query="$0.000063"),
    BenchmarkItem(engine="Custom S3 + Iceberg", carrier_lookup_ms=451.0, allele_freq_ms=528.0, omop_join_ms=781.0, cost_per_query="$0.000063"),
    BenchmarkItem(engine="Delta Lake on S3", carrier_lookup_ms=418.0, allele_freq_ms=495.0, omop_join_ms=726.0, cost_per_query="$0.000063"),
    BenchmarkItem(engine="Amazon Aurora PostgreSQL (Serverless v2)", carrier_lookup_ms=49.0, allele_freq_ms=418.0, omop_join_ms=93.0, cost_per_query="$0.000010"),
    BenchmarkItem(engine="Amazon RDS PostgreSQL", carrier_lookup_ms=71.0, allele_freq_ms=572.0, omop_join_ms=143.0, cost_per_query="$0.000010"),
    BenchmarkItem(engine="Hail VDS (Spark)", carrier_lookup_ms=1078.0, allele_freq_ms=1375.0, omop_join_ms=2310.0, cost_per_query="$0.000079"),
    BenchmarkItem(engine="AWS HealthOmics Variant Store", carrier_lookup_ms=480.0, allele_freq_ms=590.0, omop_join_ms=890.0, cost_per_query="$0.000085"),
]


@router.get("", response_model=List[BenchmarkItem])
def get_benchmarks():
    """Returns latency SLA and cost comparisons across all 7 storage architectures."""
    return BENCHMARK_DATA
