from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from services.incrementality.models import EconomicHurdleResult


class MetaPlacementRow(BaseModel):
    publisher_platform: str = Field(..., description="facebook, instagram, audience_network, messenger")
    platform_position: str = Field(..., description="feed, story, reel, explore, rewarded_video, etc.")
    spend: Decimal = Field(..., ge=0)
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    conversions: Decimal = Field(..., ge=0)
    conversion_value: Decimal = Field(..., ge=0)

    @property
    def roas(self) -> Decimal | None:
        if self.spend > Decimal(0):
            return self.conversion_value / self.spend
        return None

    @property
    def cpc(self) -> Decimal | None:
        if self.clicks > 0:
            return self.spend / Decimal(self.clicks)
        return None

    @property
    def ctr(self) -> Decimal:
        if self.impressions > 0:
            return Decimal(self.clicks) / Decimal(self.impressions)
        return Decimal(0)


class MetaAttributionWindowSplit(BaseModel):
    click_7d_conversions: Decimal = Field(..., ge=0)
    click_7d_value: Decimal = Field(..., ge=0)
    click_1d_conversions: Decimal = Field(..., ge=0)
    click_1d_value: Decimal = Field(..., ge=0)
    view_1d_conversions: Decimal = Field(..., ge=0)
    view_1d_value: Decimal = Field(..., ge=0)

    total_reported_conversions: Decimal = Field(..., ge=0)
    total_reported_value: Decimal = Field(..., ge=0)

    view_through_dependency_ratio: Decimal = Field(
        ...,
        description="Share of conversions derived purely from 1-day view-through without a click",
    )
    blended_roas: Decimal
    click_only_roas: Decimal
    ghost_roas_inflation_pct: Decimal = Field(
        ...,
        description="Percentage by which 1-day view attribution inflates reported ROAS over click-only ROAS",
    )


class MetaAudienceCapAudit(BaseModel):
    configured_cap_pct: Decimal = Field(..., description="Advertiser configured Existing Customer Budget Cap (e.g. 5%)")
    actual_existing_customer_spend: Decimal = Field(..., ge=0)
    actual_new_customer_spend: Decimal = Field(..., ge=0)
    actual_existing_spend_pct: Decimal = Field(..., ge=0)
    cap_exceeded: bool
    customer_list_age_days: Optional[int] = Field(default=None)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    finding: str


class MetaCreativeFormatRow(BaseModel):
    format_type: Literal["CATALOG_DPA", "VIDEO_REELS", "VIDEO_FEED", "STATIC_IMAGE", "CAROUSEL"]
    spend: Decimal = Field(..., ge=0)
    share: Decimal = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    conversions: Decimal = Field(..., ge=0)
    conversion_value: Decimal = Field(..., ge=0)
    roas: Decimal


class MetaAscAuditReport(BaseModel):
    schema_version: str = Field(default="1.0.0")
    generated_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    account_id: str
    account_name: str
    currency_code: str
    start_date: dt.date
    end_date: dt.date

    total_spend: Decimal = Field(..., ge=0)
    total_conversion_value: Decimal = Field(..., ge=0)
    blended_roas: Decimal
    click_only_roas: Decimal

    # 5 Core Checks
    placement_rows: list[MetaPlacementRow] = Field(default_factory=list)
    audience_network_spend_share: Decimal
    audience_network_severity: Literal["SAFE", "WARNING", "CRITICAL"]

    attribution_split: MetaAttributionWindowSplit
    audience_cap_audit: MetaAudienceCapAudit
    creative_formats: list[MetaCreativeFormatRow] = Field(default_factory=list)

    hurdle: Optional[EconomicHurdleResult] = None
    net_profit_per_euro_spend: Optional[Decimal] = None

    recommendations: list[str] = Field(default_factory=list)

    @field_validator("account_id")
    @classmethod
    def normalize_account_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned.startswith("act_"):
            return f"act_{cleaned}"
        return cleaned
