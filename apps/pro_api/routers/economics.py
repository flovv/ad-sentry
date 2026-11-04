from __future__ import annotations

from decimal import Decimal
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from services.incrementality.economics import calculate_breakeven_hurdle
from services.incrementality.models import EconomicHurdleResult

router = APIRouter(prefix="/economics", tags=["Economics"])


class HurdleRequest(BaseModel):
    contribution_margin_rate: Decimal
    notes: Optional[list[str]] = None


@router.post("/breakeven", response_model=EconomicHurdleResult)
def get_breakeven_hurdle(req: HurdleRequest) -> EconomicHurdleResult:
    return calculate_breakeven_hurdle(
        contribution_margin_rate=req.contribution_margin_rate,
        notes=req.notes,
    )
