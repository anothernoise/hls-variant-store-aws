"""
AWS Genomic Variant Store — FastAPI Middle Layer Service.
Provides RESTful endpoints for population-scale genomic analytics,
multi-engine query routing, and real-time telemetry.
"""

from datetime import datetime, timezone
import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.routers import engines, benchmarks
from api.schemas import HealthResponse

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("variant_store_api")

app = FastAPI(
    title="AWS Genomic Variant Store — Middle Layer API",
    description=(
        "Production-grade RESTful API middle layer orchestrating queries across "
        "7 AWS genomic storage engine architectures (S3 Tables, Iceberg, Delta Lake, "
        "Hail VDS, Aurora PostgreSQL, RDS PostgreSQL, HealthOmics)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local Dash UI or external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(engines.router)
app.include_router(benchmarks.router)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """System health check and version verification endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
