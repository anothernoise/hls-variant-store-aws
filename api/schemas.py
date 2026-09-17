"""
Pydantic Schemas for FastAPI Middle Layer.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    version: str = Field(default="1.0.0", description="API Version")
    timestamp: str = Field(description="ISO 8601 UTC timestamp")


class EngineMetadataResponse(BaseModel):
    id: str = Field(description="Unique engine identifier")
    name: str = Field(description="Human readable engine display name")
    display_order: int = Field(default=99, description="UI sorting order")
    database: str = Field(description="Database or catalog reference")
    table_name: str = Field(description="Target table name")
    architecture: Dict[str, str] = Field(default_factory=dict, description="Physical storage architecture metadata")
    telemetry_profile: Dict[str, Any] = Field(default_factory=dict, description="Typical baseline telemetry metrics")


class QueryTelemetry(BaseModel):
    engine: str = Field(description="Target engine name")
    latency_ms: float = Field(description="Query latency in milliseconds")
    scanned_bytes: int = Field(default=0, description="Data scanned in bytes")
    query_type: str = Field(default="Query Execution", description="Analytical query category")
    mode: str = Field(description="'online' (live AWS Athena/Data API) or 'offline' (simulation)")
    target_database: Optional[str] = Field(default=None, description="Actual database queried")
    status: Optional[str] = Field(default=None, description="Engine status flag")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


class QueryResultResponse(BaseModel):
    records: List[Dict[str, Any]] = Field(default_factory=list, description="Tabular records returned by query")
    telemetry: QueryTelemetry = Field(description="Execution telemetry and SLA profile")
    sql: Optional[str] = Field(default=None, description="SQL query executed against the engine")


class BenchmarkItem(BaseModel):
    engine: str = Field(description="Engine name")
    carrier_lookup_ms: float = Field(description="Pathogenic carrier point lookup latency (ms)")
    allele_freq_ms: float = Field(description="Cohort allele frequency aggregation latency (ms)")
    omop_join_ms: float = Field(description="Multimodal clinical OMOP join latency (ms)")
    cost_per_query: str = Field(description="Estimated dollar cost per query execution")
