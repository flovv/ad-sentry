from __future__ import annotations

import datetime as dt
from decimal import Decimal
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class EvidenceClass(str, Enum):
    REPORTED = "REPORTED"
    OBSERVATIONAL = "OBSERVATIONAL"
    EXPERIMENTAL = "EXPERIMENTAL"


class CoverageStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class DeliveryRow(BaseModel):
    customer_id: str = Field(..., description="Google Ads 10-digit customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    campaign_name: str = Field(..., description="Campaign Name")
    advertising_channel_type: str = Field(
        default="PERFORMANCE_MAX",
        description="Advertising channel type: PERFORMANCE_MAX or DEMAND_GEN",
    )
    date: dt.date = Field(..., description="Reporting date")
    channel: str = Field(
        ...,
        description="Reported channel (e.g. Google Search, Search Partners, Display, YouTube, Discover, Gmail, Maps)",
    )
    uses_product_data: bool | None = Field(
        default=None,
        description="Whether the ad unit used merchant center product data",
    )
    uses_video: bool | None = Field(
        default=None,
        description="Whether the ad unit used video assets",
    )
    currency_code: str = Field(..., min_length=3, max_length=3, description="ISO 4217 3-letter currency code")
    cost_micros: int = Field(..., ge=0, description="Cost in micros (1 unit = 1,000,000 micros)")
    impressions: int = Field(..., ge=0, description="Impression count")
    clicks: int = Field(..., ge=0, description="Click count")
    conversions: Decimal = Field(..., ge=0, description="Reported conversion count")
    conversion_value: Decimal = Field(..., ge=0, description="Reported conversion value in account currency")
    view_through_conversions: Decimal = Field(
        default=Decimal(0),
        ge=0,
        description="Reported view-through conversions (conversions following ad view without click)",
    )

    @field_validator("customer_id")
    @classmethod
    def normalize_customer_id(cls, v: str) -> str:
        cleaned = v.replace("-", "").strip()
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError(f"Customer ID must be a 10-digit string, got '{v}'")
        return cleaned

    @property
    def cost(self) -> Decimal:
        return Decimal(self.cost_micros) / Decimal(1_000_000)

    @property
    def roas(self) -> Decimal | None:
        c = self.cost
        if c > Decimal(0):
            return self.conversion_value / c
        return None


class CoverageSummary(BaseModel):
    status: Literal["COMPLETE", "PARTIAL", "UNAVAILABLE"]
    segmented_cost_micros: int = Field(..., ge=0)
    unsegmented_cost_micros: int = Field(..., ge=0)
    difference_micros: int = Field(
        ...,
        description="Raw difference: unsegmented_cost_micros - segmented_cost_micros. Never hidden by max(0, diff).",
    )
    coverage_ratio: Decimal | None = Field(
        default=None,
        description="Segmented cost divided by unsegmented cost, or None if unsegmented is 0.",
    )
    reasons: list[str] = Field(default_factory=list, description="Explanations for partial or unavailable coverage.")


class CrossCampaignOverlapSummary(BaseModel):
    pmax_cost: Decimal
    demand_gen_cost: Decimal
    total_cost: Decimal
    shared_surfaces: list[str] = Field(default_factory=lambda: ["YouTube", "Discover", "Gmail"])
    surface_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    overlap_severity: Literal["NONE", "LOW", "MEDIUM", "HIGH"]
    pmax_view_through_ratio: Decimal
    demand_gen_view_through_ratio: Decimal
    recommendations: list[str] = Field(default_factory=list)


class DeliveryReport(BaseModel):
    schema_version: str = Field(default="1.0.0")
    api_version: str = Field(default="v26")
    generated_at: dt.datetime
    customer_id: str
    currency_code: str
    timezone: str
    start_date: dt.date
    end_date: dt.date
    rows: list[DeliveryRow] = Field(default_factory=list)
    coverage: CoverageSummary
    warnings: list[str] = Field(default_factory=list)
    included_channel_types: list[str] = Field(default_factory=lambda: ["PERFORMANCE_MAX"])
    cross_campaign_overlap: CrossCampaignOverlapSummary | None = None

    @field_validator("customer_id")
    @classmethod
    def normalize_customer_id(cls, v: str) -> str:
        cleaned = v.replace("-", "").strip()
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError(f"Customer ID must be a 10-digit string, got '{v}'")
        return cleaned

    @model_validator(mode="after")
    def validate_date_range(self) -> DeliveryReport:
        if self.start_date > self.end_date:
            raise ValueError(f"start_date {self.start_date} cannot be after end_date {self.end_date}")
        return self

    @property
    def total_cost_micros(self) -> int:
        return sum(r.cost_micros for r in self.rows)

    @property
    def total_cost(self) -> Decimal:
        return Decimal(self.total_cost_micros) / Decimal(1_000_000)

    @property
    def total_conversions(self) -> Decimal:
        return sum((r.conversions for r in self.rows), Decimal(0))

    @property
    def total_conversion_value(self) -> Decimal:
        return sum((r.conversion_value for r in self.rows), Decimal(0))

    @property
    def total_impressions(self) -> int:
        return sum(r.impressions for r in self.rows)

    @property
    def total_clicks(self) -> int:
        return sum(r.clicks for r in self.rows)

    @property
    def reported_roas(self) -> Decimal | None:
        cost = self.total_cost
        if cost > Decimal(0):
            return self.total_conversion_value / cost
        return None


class SearchInsightRow(BaseModel):
    customer_id: str
    campaign_id: str
    campaign_name: str
    category_label: str = Field(..., description="Search term category label returned by the API")
    date: dt.date | None = Field(default=None, description="Segment date if segmented by day")
    clicks: int = Field(default=0, ge=0)
    conversions: Decimal = Field(default=Decimal(0), ge=0)
    conversion_value: Decimal = Field(default=Decimal(0), ge=0)
    impressions: int = Field(default=0, ge=0)
    search_volume: int | None = Field(
        default=None,
        ge=0,
        description="Search volume metric if returned by API. Note: Cost is NEVER present on search insight resource.",
    )

    @field_validator("customer_id")
    @classmethod
    def normalize_customer_id(cls, v: str) -> str:
        return v.replace("-", "").strip()


class BrandDiagnosticSummary(BaseModel):
    classifier_version: str = Field(default="1.0.0")
    brand_dictionary: list[str] = Field(default_factory=list)
    classifiable_query_share: Decimal = Field(
        ...,
        description="Share of queries/volume that could be classified with the user-supplied dictionary",
    )
    brand_query_share: Decimal = Field(..., description="Share of classifiable queries matched to brand")
    generic_query_share: Decimal = Field(..., description="Share of classifiable queries matched to generic")
    unknown_query_share: Decimal = Field(..., description="Share of query data unclassifiable or unavailable")
    notes: list[str] = Field(default_factory=list)


class SearchInsightReport(BaseModel):
    schema_version: str = Field(default="1.0.0")
    api_version: str = Field(default="v26")
    generated_at: dt.datetime
    customer_id: str
    start_date: dt.date
    end_date: dt.date
    rows: list[SearchInsightRow] = Field(default_factory=list)
    brand_diagnostic: BrandDiagnosticSummary | None = None
    warnings: list[str] = Field(
        default_factory=lambda: [
            "Search term insights are informational search-demand categories and do NOT include cost metrics.",
            "Do not infer brand-search spend or budget allocation from search-term insights.",
        ]
    )

    @field_validator("customer_id")
    @classmethod
    def normalize_customer_id(cls, v: str) -> str:
        return v.replace("-", "").strip()


class CampaignInfo(BaseModel):
    id: str
    name: str
    status: str = Field(..., description="ENABLED, PAUSED, REMOVED")
    advertising_channel_type: str = Field(default="PERFORMANCE_MAX")
    bidding_strategy_type: str | None = None
    target_roas: float | None = None


class AccountInfo(BaseModel):
    customer_id: str
    descriptive_name: str
    currency_code: str
    time_zone: str
    can_manage_clients: bool = False

    @field_validator("customer_id")
    @classmethod
    def normalize_customer_id(cls, v: str) -> str:
        return v.replace("-", "").strip()
