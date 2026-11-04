from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

from pmax_sentry_core.models import EvidenceClass
from services.incrementality.models import (
    EconomicHurdleResult,
    ExperimentPlan,
    ExperimentResultAnalysis,
    ObservationalDiagnosticResult,
    UncertaintyInterval,
)


class DecisionContract(BaseModel):
    contract_version: str = Field(default="1.0.0", description="Semantic version of decision contract specification")
    contract_id: str
    generated_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    customer_id: str
    campaign_ids: list[str]
    date_range: tuple[dt.date, dt.date]
    timezone: str
    evidence_class: EvidenceClass

    claim: str
    evidence_references: list[str] = Field(default_factory=list)
    reported_metrics: dict[str, Any] = Field(default_factory=dict)
    estimate_and_uncertainty_interval: Optional[UncertaintyInterval] = None

    model_version_and_diagnostics: Optional[dict[str, Any]] = None
    estimand_and_outcome_definition: Optional[str] = None
    experiment_design: Optional[ExperimentPlan] = None
    power_mde_and_lag_treatment: Optional[dict[str, Any]] = None
    contribution_margin_and_breakeven_hurdle: Optional[EconomicHurdleResult] = None

    assumptions_and_limitations: list[str] = Field(default_factory=list)
    recommendation_type: Literal["REVIEW", "SCENARIO", "EXPERIMENT", "NO_ACTION"]
    approval_required: Literal[True] = True
    valid_until: dt.date
    next_review_date: Optional[dt.date] = None
    data_retention_reference: str = Field(
        default="Data retention governed by customer workspace policy. Reporting records only; no live mutation capabilities."
    )
