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
    table: Optional[str] = Field(default=None, description="Actual table or view inspected")
    rows_retrieved: Optional[int] = Field(default=0, description="Total number of rows returned")
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


class BenchmarkRunRequest(BaseModel):
    mode: str = Field(default="simulated", pattern="^(simulated|live)$", description="Execution mode: 'simulated' or 'live'")
    cohort_size: int = Field(default=100, ge=1, le=2500, description="Cohort size to benchmark (1-2500)")
    engines: Optional[List[str]] = Field(default=None, description="Optional target engines subset")


class BenchmarkRunResponse(BaseModel):
    mode: str = Field(description="Execution mode ('live' or 'simulated')")
    cohort_size: int = Field(description="Target cohort size")
    execution_duration_ms: float = Field(description="Total benchmark run duration in milliseconds")
    engine_summary: List[BenchmarkItem] = Field(default_factory=list, description="Per-engine aggregated latency & cost items")
    query_benchmarks: List[Dict[str, Any]] = Field(default_factory=list, description="Granular query scenario results")
    n1_benchmarks: Dict[str, Any] = Field(default_factory=dict, description="N+1 ingestion append metrics")
    cohort_scaling_curve: List[Dict[str, Any]] = Field(default_factory=list, description="Cross-cohort scaling curve points")
    ai_analysis: Dict[str, Any] = Field(default_factory=dict, description="AI architectural reasoning and performance recommendation")



class VariantRecordInput(BaseModel):
    reference_name: str = Field(description="Chromosome / contig name (e.g. chr17)")
    start: int = Field(description="1-based start genomic position")
    end: int = Field(description="1-based end genomic position")
    reference_bases: str = Field(description="Reference allele bases (e.g. A)")
    alternate_bases: str = Field(description="Alternate allele bases (e.g. G)")
    sample_id: str = Field(description="Sample / patient identifier")
    genotype: str = Field(default="0/1", description="Genotype call (e.g. 0/1, 1/1)")
    qual: float = Field(default=99.0, description="Phred variant quality score")
    filter: str = Field(default="PASS", description="VCF filter status")
    dp: int = Field(default=30, description="Total read depth")
    gq: int = Field(default=99, description="Genotype quality score")
    allele_depth: str = Field(default="15,15", description="Allelic depths (AD)")
    attributes: str = Field(default="{}", description="JSON serialized variant annotations (gene, clnsig)")


class FeedBatchRequest(BaseModel):
    cohort_id: str = Field(default="online_feed_v1", description="Cohort / batch identifier")
    records: List[VariantRecordInput] = Field(default_factory=list, description="List of structured variant calls to ingest")


class FeedBatchResponse(BaseModel):
    batch_id: str = Field(description="Unique batch identifier")
    engine: str = Field(description="Target engine identifier stamped on ingested records")
    records_ingested: int = Field(description="Number of variant calls successfully ingested")
    duration_ms: float = Field(description="Ingestion execution duration in milliseconds")
    status: str = Field(default="COMPLETED", description="Batch ingestion status")
    target_table: str = Field(description="Target table where records were appended")


class ComponentCheck(BaseModel):
    name: str = Field(description="Subsystem or resource check component name")
    status: str = Field(description="Health status: pass, warn, or fail")
    observed_value: Optional[str] = Field(default=None, description="Observed resource or connectivity status")
    latency_ms: float = Field(default=0.0, description="Component probe latency in ms")


class EngineHealthResponse(BaseModel):
    engine_id: str = Field(description="Unique engine identifier")
    engine_name: str = Field(description="Human-readable storage engine name")
    status: str = Field(description="RFC health check status: pass, warn, or fail")
    deployment_status: str = Field(description="AWS infrastructure status: ACTIVE, AVAILABLE, NOT_DEPLOYED, DEGRADED")
    target_resource: str = Field(description="Physical AWS target resource (S3 bucket, Glue DB, RDS cluster)")
    latency_ms: float = Field(description="Health check probe duration in ms")
    mode: str = Field(description="Execution mode: online or offline")
    checks: Dict[str, ComponentCheck] = Field(default_factory=dict, description="Detailed component checks")
    timestamp: str = Field(description="ISO 8601 UTC timestamp")


class EngineHealthSummaryResponse(BaseModel):
    status: str = Field(description="Overall health status: healthy, degraded, or unhealthy")
    total_engines: int = Field(description="Total configured storage engines")
    active_engines: int = Field(description="Count of currently active/available storage engines")
    not_deployed_engines: int = Field(description="Count of un-deployed storage engines")
    probe_latency_ms: float = Field(description="Total probe duration in ms")
    engines: Dict[str, EngineHealthResponse] = Field(description="Map of engine_id to health response")
    timestamp: str = Field(description="ISO 8601 UTC timestamp")


