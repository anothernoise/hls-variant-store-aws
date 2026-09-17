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

