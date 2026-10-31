from __future__ import annotations

import datetime as dt
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field

from pmax_sentry_core.models import EvidenceClass


class UncertaintyInterval(BaseModel):
    point_estimate: Decimal
    ci_lower_95: Decimal
    ci_upper_95: Decimal

    @property
    def formatted(self) -> str:
        return f"{self.point_estimate:.2f} (95% CI: [{self.ci_lower_95:.2f}, {self.ci_upper_95:.2f}])"


class AssociationDiagnostic(BaseModel):
    metric_name: str = Field(default="Organic/Direct Revenue Sensitivity")
    coefficient: Decimal
    p_value: float
    interpretation: str
    caution: str = Field(
        default="This is an observational association diagnostic and NOT a causal cannibalization proof. Causal claims require experimental validation."
    )


class ObservationalDiagnosticResult(BaseModel):
    status: Literal["COMPLETED", "LOW_CONFIDENCE", "INSUFFICIENT_DATA"]
    evidence_class: EvidenceClass = EvidenceClass.OBSERVATIONAL
    model_version: str = Field(default="1.0.0-ols-covariates")
    dataset_id: str
    matured_date_window: tuple[dt.date, dt.date]
    modeled_iroas_estimate: Optional[UncertaintyInterval] = None
    platform_reported_roas: Decimal
    r_squared: Optional[float] = None
    p_value: Optional[float] = None
    association_diagnostic: Optional[AssociationDiagnostic] = None
    controls_included: list[str] = Field(default_factory=list)
    omitted_controls: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ExperimentPowerAnalysis(BaseModel):
    customer_id: str
    baseline_daily_revenue: Decimal
    baseline_revenue_cv: float
    alpha: float = 0.05
    power: float = 0.80
    treatment_split: float = 0.50
    mde_pct: float
    recommended_duration_days: int
    conversion_lag_days: int
    total_study_duration_days: int
    feasibility: Literal["FEASIBLE", "BORDERLINE", "UNDERPOWERED"]
    notes: list[str] = Field(default_factory=list)


class ExperimentPlan(BaseModel):
    plan_id: str
    customer_id: str
    design_type: Literal["PLATFORM_NATIVE_SPLIT", "GEO_BASED_STEP_TEST"]
    estimand: str = Field(
        default="Total incremental business revenue per incremental media dollar spent on PMax"
    )
    treatment_units: list[str]
    control_units: list[str]
    pre_period_days: int
    test_period_days: int
    conversion_lag_maturation_days: int
    power_mde_pct: float
    alpha: float = 0.05
    power: float = 0.80
    allowed_campaign_changes: list[str]
    prohibited_campaign_changes: list[str]
    contamination_risks: list[str]
    stop_conditions: list[str]
    interpretation_limits: list[str]


class ExperimentResultAnalysis(BaseModel):
    test_id: str
    evidence_class: EvidenceClass = EvidenceClass.EXPERIMENTAL
    analysis_method: str = "Differences-in-Differences (DiD)"
    test_period: tuple[dt.date, dt.date]
    pre_period: tuple[dt.date, dt.date]
    measured_iroas: UncertaintyInterval
    incremental_revenue: Decimal
    incremental_spend: Decimal
    p_value: float
    statistically_significant: bool
    conversion_lag_treated: bool
    conclusion: str
    assumptions: list[str] = Field(default_factory=list)


class EconomicHurdleResult(BaseModel):
    contribution_margin_rate: Decimal = Field(..., description="Contribution margin rate before ad spend (mu)")
    breakeven_iroas: Decimal = Field(..., description="Break-even incremental ROAS: 1 / mu")
    formula: str = "Break-even iROAS = 1 / mu"
    units: str = "Incremental Revenue / Incremental Spend"
    input_source: str = "Advertiser-supplied contribution economics"
    scenario_assumptions: list[str] = Field(default_factory=list)
    marginal_spend_guidance: str
