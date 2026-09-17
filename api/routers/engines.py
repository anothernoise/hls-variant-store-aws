"""
FastAPI Router for Storage Engines and Genomic Analytics Endpoints.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    EngineMetadataResponse,
    QueryResultResponse,
    QueryTelemetry,
    FeedBatchRequest,
    FeedBatchResponse,
    EngineHealthResponse,
    EngineHealthSummaryResponse
)
from app.backend import VariantStoreBackend

logger = logging.getLogger("variant_store_api.engines")
router = APIRouter(prefix="/api/v1/engines", tags=["Engines & Queries"])

backend = VariantStoreBackend()


def resolve_engine_name(engine_id_or_name: str) -> str:
    """Resolves an engine slug or display name to canonical engine name."""
    configs = VariantStoreBackend.ENGINE_CONFIGS
    # Direct match by name
    if engine_id_or_name in configs:
        return engine_id_or_name
    # Match by id slug
    for name, cfg in configs.items():
        if cfg.get("id") == engine_id_or_name:
            return name
    raise HTTPException(
        status_code=404,
        detail=f"Storage engine '{engine_id_or_name}' not found. Valid engines: {list(configs.keys())}"
    )


@router.get("", response_model=List[EngineMetadataResponse])
def list_engines():
    """Lists all configured AWS genomic storage engines and their architecture profiles."""
    configs = VariantStoreBackend.ENGINE_CONFIGS
    result = []
    for name, cfg in configs.items():
        result.append(EngineMetadataResponse(
            id=cfg.get("id", name.lower().replace(" ", "_")),
            name=name,
            display_order=cfg.get("display_order", 99),
            database=cfg.get("database", "default"),
            table_name=cfg.get("table_name", "variants"),
            architecture=cfg.get("architecture", {}),
            telemetry_profile=cfg.get("telemetry_profile", {})
        ))
    result.sort(key=lambda x: x.display_order)
    return result


@router.get("/health/all", response_model=EngineHealthSummaryResponse)
def get_all_engines_health(
    offline: bool = Query(default=False, description="Toggle offline synthetic simulation mode")
):
    """Retrieves aggregated health and readiness report across all 7 genomic storage engines."""
    summary = backend.check_all_engines_health(offline=offline)
    return EngineHealthSummaryResponse(**summary)


@router.get("/{engine_id}", response_model=EngineMetadataResponse)
def get_engine_metadata(engine_id: str):
    """Retrieves physical storage architecture details for a specific engine."""
    canonical_name = resolve_engine_name(engine_id)
    cfg = VariantStoreBackend.get_engine_config(canonical_name)
    return EngineMetadataResponse(
        id=cfg.get("id", engine_id),
        name=canonical_name,
        display_order=cfg.get("display_order", 99),
        database=cfg.get("database", "default"),
        table_name=cfg.get("table_name", "variants"),
        architecture=cfg.get("architecture", {}),
        telemetry_profile=cfg.get("telemetry_profile", {})
    )


@router.get("/{engine_id}/health", response_model=EngineHealthResponse)
def get_engine_health(
    engine_id: str,
    offline: bool = Query(default=False, description="Toggle offline synthetic simulation mode")
):
    """Executes runtime health and availability probe for a specific genomic storage engine."""
    canonical_name = resolve_engine_name(engine_id)
    health = backend.check_engine_health(canonical_name, offline=offline)
    return EngineHealthResponse(**health)


@router.get("/{engine_id}/allele-frequencies", response_model=QueryResultResponse)
def get_allele_frequencies(
    engine_id: str,
    offline: bool = Query(default=False, description="Toggle offline synthetic simulation mode")
):
    """Executes population cohort allele frequency aggregation against the engine."""
    canonical_name = resolve_engine_name(engine_id)
    df, telemetry = backend.get_allele_frequencies(canonical_name, offline=offline)
    sql = backend.build_engine_sql(canonical_name, query_kind="af")
    return QueryResultResponse(
        records=df.to_dict("records"),
        telemetry=QueryTelemetry(**telemetry),
        sql=sql
    )


@router.get("/{engine_id}/carrier-lookup", response_model=QueryResultResponse)
def get_carrier_lookup(
    engine_id: str,
    gene: str = Query(default="APP", description="Target gene symbol"),
    offline: bool = Query(default=False, description="Toggle offline simulation mode")
):
    """Point query for pathogenic variant carriers (e.g. APP rs63750066)."""
    canonical_name = resolve_engine_name(engine_id)
    df, telemetry = backend.get_pathogenic_carriers(canonical_name, gene=gene, offline=offline)
    sql = backend.build_engine_sql(canonical_name, query_kind="carriers", gene=gene)
    return QueryResultResponse(
        records=df.to_dict("records"),
        telemetry=QueryTelemetry(**telemetry),
        sql=sql
    )


@router.get("/{engine_id}/gene-burden", response_model=QueryResultResponse)
def get_gene_burden(
    engine_id: str,
    gene: str = Query(default="APP", description="Target gene symbol"),
    offline: bool = Query(default=False, description="Toggle offline simulation mode")
):
    """Rollup of sample-level mutation allele burden."""
    canonical_name = resolve_engine_name(engine_id)
    df, telemetry = backend.get_gene_burden(canonical_name, gene=gene, offline=offline)
    sql = backend.build_engine_sql(canonical_name, query_kind="burden", gene=gene)
    return QueryResultResponse(
        records=df.to_dict("records"),
        telemetry=QueryTelemetry(**telemetry),
        sql=sql
    )


@router.get("/{engine_id}/omop-phenotype-join", response_model=QueryResultResponse)
def get_omop_phenotype_join(
    engine_id: str,
    offline: bool = Query(default=False, description="Toggle offline simulation mode")
):
    """Federated cross-modal join between genomic variant calls and OMOP clinical person/condition tables."""
    canonical_name = resolve_engine_name(engine_id)
    df, telemetry = backend.get_omop_phenotype_join(canonical_name, offline=offline)
    sql = backend.build_engine_sql(canonical_name, query_kind="omop")
    return QueryResultResponse(
        records=df.to_dict("records"),
        telemetry=QueryTelemetry(**telemetry),
        sql=sql
    )


@router.get("/{engine_id}/raw-records", response_model=QueryResultResponse)
def get_raw_records(
    engine_id: str,
    table_name: str = Query(default="variants", description="Table: variants, person, or condition_occurrence"),
    chromosome: str = Query(default="All", description="Filter chromosome (e.g. chr21)"),
    sample_id: str = Query(default="All", description="Filter sample ID"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max rows to retrieve"),
    offline: bool = Query(default=False, description="Toggle offline simulation mode")
):
    """Direct table inspection with SQL query preview and column filtering."""
    canonical_name = resolve_engine_name(engine_id)
    df, telemetry, sql = backend.get_raw_store_data(
        engine=canonical_name,
        table_name=table_name,
        chromosome=chromosome,
        sample_id=sample_id,
        limit=limit,
        offline=offline
    )
    return QueryResultResponse(
        records=df.to_dict("records"),
        telemetry=QueryTelemetry(**telemetry),
        sql=sql
    )


@router.post("/{engine_id}/feed", response_model=FeedBatchResponse, status_code=201)
def feed_engine_batch(
    engine_id: str,
    payload: FeedBatchRequest
):
    """Ingests a batch of variant records into the target engine store and stamps the engine name."""
    canonical_name = resolve_engine_name(engine_id)
    records_dict = [rec.model_dump() for rec in payload.records]
    result = backend.feed_engine(
        engine=canonical_name,
        records=records_dict,
        cohort_id=payload.cohort_id
    )
    return FeedBatchResponse(**result)
