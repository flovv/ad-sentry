from __future__ import annotations

import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from apps.pro_api.auth import MaskingFormatter
from apps.pro_api.routers.contracts import router as contracts_router
from apps.pro_api.routers.diagnostics import router as diagnostics_router
from apps.pro_api.routers.economics import router as economics_router
from apps.pro_api.routers.experiments import router as experiments_router
from apps.pro_api.routers.ingestion import router as ingestion_router
from apps.pro_api.routers.reports import router as reports_router
from apps.pro_api.routers.workspaces import router as workspaces_router
from pmax_sentry_core.client import PINNED_API_VERSION

# Configure logging with sensitive data masking
logger = logging.getLogger("pmax_sentry")
handler = logging.StreamHandler()
handler.setFormatter(MaskingFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(
    title="PMax Sentry Pro API",
    description="Hosted, read-only measurement service for Google Ads Performance Max incrementality and causal validation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspaces_router)
app.include_router(reports_router)
app.include_router(ingestion_router)
app.include_router(diagnostics_router)
app.include_router(experiments_router)
app.include_router(economics_router)
app.include_router(contracts_router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "pmax-sentry-pro",
        "version": "0.1.0",
        "pinned_api_version": PINNED_API_VERSION,
        "read_only": "true",
    }


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>PMax Sentry Pro — Measurement Dashboard</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0b0f19; color: #f3f4f6; margin: 0; padding: 2rem; }
        .container { max-width: 960px; margin: 0 auto; }
        .card { background: #161e2e; border: 1px solid #374151; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }
        h1, h2, h3 { color: #60a5fa; margin-top: 0; }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
        .badge-reported { background: #1e3a8a; color: #93c5fd; }
        .badge-obs { background: #854d0e; color: #fef08a; }
        .badge-exp { background: #065f46; color: #a7f3d0; }
        .btn { background: #2563eb; color: #fff; padding: 0.6rem 1.2rem; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: 500; }
        .btn:hover { background: #1d4ed8; }
        pre { background: #030712; padding: 1rem; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; color: #e5e7eb; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>PMax Sentry Pro</h1>
        <p style="color: #9ca3af;">Deterministic Performance Max delivery observability, data quality preflight, and causal measurement.</p>
        
        <div class="card">
          <h2>Three-Stage Measurement Discipline</h2>
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
            <div style="background: #111827; padding: 1rem; border-radius: 6px;">
              <span class="badge badge-reported">STAGE 1: REPORTED</span>
              <h3>Delivery Observability</h3>
              <p style="font-size: 0.9rem; color: #9ca3af;">Channel & format breakdown, total-vs-segmented reconciliation, and search demand categories.</p>
            </div>
            <div style="background: #111827; padding: 1rem; border-radius: 6px;">
              <span class="badge badge-obs">STAGE 2: OBSERVATIONAL</span>
              <h3>Historical Diagnosis</h3>
              <p style="font-size: 0.9rem; color: #9ca3af;">Matured data preflight, lag cutoffs, covariate controls, and organic association diagnostics.</p>
            </div>
            <div style="background: #111827; padding: 1rem; border-radius: 6px;">
              <span class="badge badge-exp">STAGE 3: EXPERIMENTAL</span>
              <h3>Causal Validation</h3>
              <p style="font-size: 0.9rem; color: #9ca3af;">Power analysis, MDE, geo/native test designs, and Difference-in-Differences measured iROAS.</p>
            </div>
          </div>
        </div>

        <div class="card">
          <h2>Pro Service Status</h2>
          <p>Read-Only API endpoints: <code>/reports</code>, <code>/ingestion</code>, <code>/diagnostics</code>, <code>/experiments</code>, <code>/economics</code>, <code>/contracts</code></p>
          <a href="/docs" class="btn">Explore OpenAPI / Swagger Docs</a>
        </div>
      </div>
    </body>
    </html>
    """
