from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from apps.pro_api.storage import tenant_store
from services.data_ingestion.models import BusinessOutcomeDataset
from services.data_ingestion.validator import DataIngestionError, parse_business_outcomes_csv

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


class UploadCsvRequest(BaseModel):
    csv_content: str
    customer_id: str
    currency_code: str
    timezone: str = "UTC"
    attribution_window_days: int = 30
    conversion_definition: str = "purchase"


@router.post("/upload-csv", response_model=BusinessOutcomeDataset)
def upload_business_outcomes(
    req: UploadCsvRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> BusinessOutcomeDataset:
    try:
        ds = parse_business_outcomes_csv(
            csv_content=req.csv_content,
            customer_id=req.customer_id,
            currency_code=req.currency_code,
            timezone=req.timezone,
            attribution_window_days=req.attribution_window_days,
            conversion_definition=req.conversion_definition,
        )
        tenant_store.store_dataset(x_workspace_id, ds)
        return ds
    except DataIngestionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets/{dataset_id}", response_model=BusinessOutcomeDataset)
def get_dataset(
    dataset_id: str,
    x_workspace_id: str = Header(default="default_ws"),
) -> BusinessOutcomeDataset:
    ds = tenant_store.get_dataset(x_workspace_id, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found in workspace {x_workspace_id}")
    return ds
