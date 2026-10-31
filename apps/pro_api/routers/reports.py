from __future__ import annotations

import datetime as dt
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pmax_sentry_core.api import fetch_pmax_delivery, fetch_search_insights
from pmax_sentry_core.models import DeliveryReport, SearchInsightReport

router = APIRouter(prefix="/reports", tags=["Reports"])


class DeliveryReportRequest(BaseModel):
    customer_id: str
    start_date: dt.date
    end_date: dt.date


class SearchInsightRequest(BaseModel):
    customer_id: str
    start_date: dt.date
    end_date: dt.date
    brand_dictionary: Optional[list[str]] = None


@router.post("/delivery", response_model=DeliveryReport)
def get_delivery_report(req: DeliveryReportRequest) -> DeliveryReport:
    try:
        return fetch_pmax_delivery(
            customer_id=req.customer_id,
            start_date=req.start_date,
            end_date=req.end_date,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search-insights", response_model=SearchInsightReport)
def get_search_insights(req: SearchInsightRequest) -> SearchInsightReport:
    try:
        return fetch_search_insights(
            customer_id=req.customer_id,
            start_date=req.start_date,
            end_date=req.end_date,
            brand_dictionary=req.brand_dictionary,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
