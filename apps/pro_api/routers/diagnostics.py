from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from apps.pro_api.storage import tenant_store
from services.data_quality.preflight import DataQualityReport, run_data_quality_preflight
from services.incrementality.diagnostic import run_incrementality_diagnostic
from services.incrementality.models import ObservationalDiagnosticResult

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


class DiagnosticRequest(BaseModel):
    dataset_id: str
    conversion_lag_days: int = 14


@router.post("/preflight", response_model=DataQualityReport)
def run_preflight_check(
    req: DiagnosticRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> DataQualityReport:
    ds = tenant_store.get_dataset(x_workspace_id, req.dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return run_data_quality_preflight(ds, lag_days=req.conversion_lag_days)


@router.post("/incrementality", response_model=ObservationalDiagnosticResult)
def run_incrementality(
    req: DiagnosticRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> ObservationalDiagnosticResult:
    ds = tenant_store.get_dataset(x_workspace_id, req.dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return run_incrementality_diagnostic(ds, lag_days=req.conversion_lag_days)
