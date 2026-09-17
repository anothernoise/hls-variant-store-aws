"""
API Client for Dash UI to communicate with FastAPI Middle Layer.
Includes automatic fallback to local backend if API server is unreachable.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import requests

logger = logging.getLogger("variant_store.api_client")


class VariantStoreApiClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.environ.get("API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self._backend = None
        self.session = requests.Session()
        self.session.trust_env = False

    @property
    def fallback_backend(self):
        if self._backend is None:
            try:
                from backend import VariantStoreBackend
            except (ImportError, ModuleNotFoundError):
                from app.backend import VariantStoreBackend
            self._backend = VariantStoreBackend()
        return self._backend

    def is_api_alive(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/api/v1/health", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

    def get_allele_frequencies(self, engine: str, offline: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        try:
            url = f"{self.base_url}/api/v1/engines/{engine}/allele-frequencies"
            resp = self.session.get(url, params={"offline": offline}, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                return pd.DataFrame(data.get("records", [])), data.get("telemetry", {})
        except Exception as e:
            logger.warning("FastAPI middle layer unreachable (%s), using direct backend", e)
        return self.fallback_backend.get_allele_frequencies(engine, offline=offline)

    def get_pathogenic_carriers(self, engine: str, gene: str = "APP", offline: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        try:
            url = f"{self.base_url}/api/v1/engines/{engine}/carrier-lookup"
            resp = self.session.get(url, params={"gene": gene, "offline": offline}, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                return pd.DataFrame(data.get("records", [])), data.get("telemetry", {})
        except Exception as e:
            logger.warning("FastAPI middle layer unreachable (%s), using direct backend", e)
        return self.fallback_backend.get_pathogenic_carriers(engine, gene=gene, offline=offline)

    def get_gene_burden(self, engine: str, gene: str = "APP", offline: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        try:
            url = f"{self.base_url}/api/v1/engines/{engine}/gene-burden"
            resp = self.session.get(url, params={"gene": gene, "offline": offline}, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                return pd.DataFrame(data.get("records", [])), data.get("telemetry", {})
        except Exception as e:
            logger.warning("FastAPI middle layer unreachable (%s), using direct backend", e)
        return self.fallback_backend.get_gene_burden(engine, gene=gene, offline=offline)

    def get_omop_phenotype_join(self, engine: str, offline: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        try:
            url = f"{self.base_url}/api/v1/engines/{engine}/omop-phenotype-join"
            resp = self.session.get(url, params={"offline": offline}, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                return pd.DataFrame(data.get("records", [])), data.get("telemetry", {})
        except Exception as e:
            logger.warning("FastAPI middle layer unreachable (%s), using direct backend", e)
        return self.fallback_backend.get_omop_phenotype_join(engine, offline=offline)

    def get_raw_store_data(
        self,
        engine: str,
        table_name: str = "variants",
        chromosome: str = "All",
        sample_id: str = "All",
        limit: int = 100,
        offline: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any], str]:
        try:
            url = f"{self.base_url}/api/v1/engines/{engine}/raw-records"
            params = {
                "table_name": table_name,
                "chromosome": chromosome,
                "sample_id": sample_id,
                "limit": limit,
                "offline": offline
            }
            resp = self.session.get(url, params=params, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                return pd.DataFrame(data.get("records", [])), data.get("telemetry", {}), data.get("sql", "")
        except Exception as e:
            logger.warning("FastAPI middle layer unreachable (%s), using direct backend", e)
        return self.fallback_backend.get_raw_store_data(
            engine=engine,
            table_name=table_name,
            chromosome=chromosome,
            sample_id=sample_id,
            limit=limit,
            offline=offline
        )

    def get_benchmarks(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/api/v1/benchmarks"
            resp = self.session.get(url, timeout=5.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    def feed_engine(
        self,
        engine: str,
        records: List[Dict[str, Any]],
        cohort_id: str = "online_feed"
    ) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/api/v1/engines/{engine}/feed"
            payload = {"cohort_id": cohort_id, "records": records}
            resp = self.session.post(url, json=payload, timeout=30.0)
            if resp.status_code in (200, 201):
                return resp.json()
        except Exception as e:
            logger.warning("FastAPI middle layer unreachable (%s), using direct backend for feed", e)
        return self.fallback_backend.feed_engine(engine=engine, records=records, cohort_id=cohort_id)

