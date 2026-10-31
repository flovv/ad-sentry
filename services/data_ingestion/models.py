from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DailyOutcomeRecord(BaseModel):
    date: dt.date = Field(..., description="Daily outcome date (YYYY-MM-DD)")
    total_business_revenue: Decimal = Field(..., ge=0, description="Total realized business revenue")
    pmax_cost: Decimal = Field(..., ge=0, description="Platform PMax cost on this date")
    pmax_conversion_value: Decimal = Field(
        ..., ge=0, description="Platform-attributed PMax conversion value on this date"
    )
    organic_revenue: Optional[Decimal] = Field(
        default=None, ge=0, description="Realized revenue from organic / direct channels"
    )
    non_pmax_spend: Optional[Decimal] = Field(
        default=None, ge=0, description="Spend on search, social, or other non-PMax ad channels"
    )
    gross_margin_rate: Optional[Decimal] = Field(
        default=None, ge=0, le=1, description="Contribution margin rate before media cost (mu)"
    )
    promo_active: Optional[bool] = Field(
        default=False, description="Whether a major promotional sale was active"
    )
    stock_constrained: Optional[bool] = Field(
        default=False, description="Whether significant inventory stock-outs occurred"
    )


class BusinessOutcomeDataset(BaseModel):
    dataset_id: str
    customer_id: str
    currency_code: str = Field(..., min_length=3, max_length=3)
    timezone: str
    attribution_window_days: int = Field(default=30, ge=1)
    conversion_definition: str = Field(default="purchase")
    records: list[DailyOutcomeRecord] = Field(default_factory=list)
    source_type: str = Field(default="csv_upload", description="csv_upload or connector")
    ingested_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))

    @property
    def start_date(self) -> dt.date | None:
        if not self.records:
            return None
        return min(r.date for r in self.records)

    @property
    def end_date(self) -> dt.date | None:
        if not self.records:
            return None
        return max(r.date for r in self.records)

    @property
    def total_revenue(self) -> Decimal:
        return sum((r.total_business_revenue for r in self.records), Decimal(0))

    @property
    def total_pmax_cost(self) -> Decimal:
        return sum((r.pmax_cost for r in self.records), Decimal(0))
