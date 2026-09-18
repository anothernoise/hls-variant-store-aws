"""
Base VariantStoreBackend orchestrating modular database and query services.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from metadata.loader import load_all_engine_metadata, get_supported_engines
except (ImportError, ModuleNotFoundError):
    from app.metadata.loader import load_all_engine_metadata, get_supported_engines

from .sql_builder import SqlBuilder
from .athena_client import AthenaClient
from .fallback_data import FallbackDataLoader
from .health import HealthChecker
from .ingestion import VariantIngestionService
from .store_explorer import StoreExplorerService


class VariantStoreBackend:
    ENGINE_CONFIGS: Dict[str, Dict[str, Any]] = load_all_engine_metadata()
    SUPPORTED_ENGINES: List[str] = get_supported_engines() or [
        "Amazon S3 Tables",
        "Custom S3 + Iceberg",
        "Delta Lake on S3",
        "Hail VDS (Spark)",
        "Amazon Aurora PostgreSQL (Serverless v2)",
        "Amazon RDS PostgreSQL",
        "AWS HealthOmics Variant Store"
    ]

    def __init__(self, default_workgroup: str = "hls-variant-store-dev", offline_mode: bool = False):
        self.workgroup = default_workgroup
        self.offline_mode = offline_mode
        self.athena_client = AthenaClient(workgroup=default_workgroup)
        self.fallback_loader = FallbackDataLoader(project_root=PROJECT_ROOT)

    @property
    def person_df(self) -> pd.DataFrame:
        return self.fallback_loader.person_df

    @property
    def cond_df(self) -> pd.DataFrame:
        return self.fallback_loader.cond_df

    @property
    def variants_df(self) -> pd.DataFrame:
        return self.fallback_loader.variants_df

    @variants_df.setter
    def variants_df(self, df: pd.DataFrame):
        self.fallback_loader.variants_df = df

    def set_offline_mode(self, enabled: bool):
        """Sets the global offline mode toggle."""
        self.offline_mode = enabled

    def _load_fallback_data(self):
        """Reloads fallback synthetic data."""
        self.fallback_loader.load_all()

    def _get_fallback_dataframe(self, query_kind: str) -> pd.DataFrame:
        """Returns deterministic baseline DataFrame for offline demo UI."""
        return FallbackDataLoader.get_fallback_dataframe(query_kind)

    def run_athena_sql(
        self,
        sql: str,
        database: str = "genomics_custom_iceberg",
        query_kind: str = "af",
        offline: Optional[bool] = None
    ) -> Tuple[pd.DataFrame, float, int, str]:
        """Execute a live SQL query via Athena, returning (DataFrame, engine_ms, scanned_bytes, mode)."""
        is_offline = self.offline_mode if offline is None else offline
        return self.athena_client.run_athena_sql(
            sql=sql,
            database=database,
            query_kind=query_kind,
            offline=is_offline
        )

    def build_engine_sql(self, engine: str, query_kind: str = "af", gene: str = "APP") -> str:
        """Generates dialect-accurate SQL targeting the specific backend engine and database."""
        config = self.get_engine_config(engine)
        return SqlBuilder.build_engine_sql(config, engine, query_kind=query_kind, gene=gene)

    def get_allele_frequencies(self, engine: str, offline: Optional[bool] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch allele frequency distributions targeting the chosen backend engine."""
        is_offline = self.offline_mode if offline is None else offline
        sql = self.build_engine_sql(engine, query_kind="af")
        config = self.get_engine_config(engine)
        db_name = config.get("database", "genomics_custom_iceberg")

        df, latency, scanned, mode = self.run_athena_sql(
            sql=sql,
            database=db_name if "/" not in db_name else "default",
            query_kind="af",
            offline=is_offline
        )

        if not df.empty:
            engine_id = config.get("id", engine.lower().replace(" ", "_"))
            df = df.copy()
            if is_offline:
                df["engine"] = "mock_data"
            else:
                df["engine"] = engine_id
            # Move engine to first column
            cols = ["engine"] + [c for c in df.columns if c != "engine"]
            df = df[cols]

        telemetry = {
            "engine": engine,
            "latency_ms": round(latency, 1),
            "scanned_bytes": scanned if "PostgreSQL" not in engine else 0,
            "query_type": "Allele Frequency Rollup",
            "mode": mode,
            "target_database": db_name
        }
        return df, telemetry

    def get_pathogenic_carriers(self, engine: str, gene: str = "APP", offline: Optional[bool] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch carrier discovery records targeting the chosen backend engine."""
        is_offline = self.offline_mode if offline is None else offline
        sql = self.build_engine_sql(engine, query_kind="carriers", gene=gene)
        config = self.get_engine_config(engine)
        db_name = config.get("database", "genomics_custom_iceberg")

        df, latency, scanned, mode = self.run_athena_sql(
            sql=sql,
            database=db_name if "/" not in db_name else "default",
            query_kind="carriers",
            offline=is_offline
        )

        if not df.empty:
            engine_id = config.get("id", engine.lower().replace(" ", "_"))
            if "engine" not in df.columns:
                df["engine"] = engine_id
            else:
                df["engine"] = df["engine"].fillna(engine_id)

        telemetry = {
            "engine": engine,
            "latency_ms": round(latency, 1),
            "scanned_bytes": scanned if "PostgreSQL" not in engine else 0,
            "query_type": "Pathogenic Carrier Point Lookup",
            "mode": mode,
            "target_database": db_name
        }
        return df, telemetry

    def get_gene_burden(self, engine: str, gene: str = "APP", offline: Optional[bool] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch gene burden rollups targeting the chosen backend engine."""
        is_offline = self.offline_mode if offline is None else offline
        sql = self.build_engine_sql(engine, query_kind="burden", gene=gene)
        config = self.get_engine_config(engine)
        db_name = config.get("database", "genomics_custom_iceberg")

        df, latency, scanned, mode = self.run_athena_sql(
            sql=sql,
            database=db_name if "/" not in db_name else "default",
            query_kind="burden",
            offline=is_offline
        )

        telemetry = {
            "engine": engine,
            "latency_ms": round(latency, 1),
            "scanned_bytes": scanned if "PostgreSQL" not in engine else 0,
            "query_type": "Gene Burden Rollup",
            "mode": mode,
            "target_database": db_name
        }
        return df, telemetry

    def get_omop_phenotype_join(self, engine: str, offline: Optional[bool] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch Genotype ↔ OMOP CDM cross-modal join targeting the chosen backend engine."""
        is_offline = self.offline_mode if offline is None else offline
        sql = self.build_engine_sql(engine, query_kind="omop")
        config = self.get_engine_config(engine)
        db_name = config.get("database", "genomics_custom_iceberg")

        df, latency, scanned, mode = self.run_athena_sql(
            sql=sql,
            database="clinical_omop",
            query_kind="omop",
            offline=is_offline
        )

        telemetry = {
            "engine": engine,
            "latency_ms": round(latency, 1),
            "scanned_bytes": scanned if "PostgreSQL" not in engine else 0,
            "query_type": "Genotype-Phenotype OMOP Join",
            "mode": mode,
            "target_database": db_name
        }
        return df, telemetry

    @classmethod
    def get_engine_config(cls, engine: str) -> Dict[str, Any]:
        """Retrieves full engine JSON configuration."""
        if not cls.ENGINE_CONFIGS:
            cls.ENGINE_CONFIGS = load_all_engine_metadata()
        if engine in cls.ENGINE_CONFIGS:
            return cls.ENGINE_CONFIGS[engine]
        for cfg in cls.ENGINE_CONFIGS.values():
            if cfg.get("id") == engine or cfg.get("canonical_name") == engine:
                return cfg
        return cls.ENGINE_CONFIGS.get("Amazon S3 Tables", next(iter(cls.ENGINE_CONFIGS.values()), {}))

    @classmethod
    def get_store_metadata(cls, engine: str) -> Dict[str, str]:
        """Returns physical storage architecture metadata for the selected engine."""
        config = cls.get_engine_config(engine)
        return config.get("architecture", {})

    def check_engine_health(self, engine: str, offline: Optional[bool] = None) -> Dict[str, Any]:
        """Health check probe conforming to IETF draft-invalle-health-check-01 specification."""
        is_offline = self.offline_mode if offline is None else offline
        config = self.get_engine_config(engine)
        return HealthChecker.check_engine_health(engine, config, offline=is_offline)

    def check_all_engines_health(self, offline: Optional[bool] = None) -> Dict[str, Any]:
        """Summary health report across all 7 AWS genomic storage engines."""
        is_offline = self.offline_mode if offline is None else offline
        return HealthChecker.check_all_engines_health(self.ENGINE_CONFIGS, offline=is_offline)

    def feed_engine(
        self,
        engine: str,
        records: List[Dict[str, Any]],
        cohort_id: str = "online_feed"
    ) -> Dict[str, Any]:
        """Ingests a batch of variant records into the target engine store."""
        config = self.get_engine_config(engine)
        updated_df, telemetry = VariantIngestionService.feed_engine(
            engine_name=engine,
            engine_config=config,
            records=records,
            existing_variants_df=self.variants_df,
            cohort_id=cohort_id
        )
        self.variants_df = updated_df
        return telemetry

    def get_raw_store_data(
        self,
        engine: str,
        table_name: str = "variants",
        chromosome: str = "All",
        sample_id: str = "All",
        limit: int = 100,
        offline: Optional[bool] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any], str]:
        """Directly retrieves raw store records with live SQL and schema-accurate fallback."""
        is_offline = self.offline_mode if offline is None else offline
        config = self.get_engine_config(engine)
        return StoreExplorerService.get_raw_store_data(
            engine_name=engine,
            engine_config=config,
            variants_df=self.variants_df,
            person_df=self.person_df,
            cond_df=self.cond_df,
            table_name=table_name,
            chromosome=chromosome,
            sample_id=sample_id,
            limit=limit,
            offline=is_offline
        )
