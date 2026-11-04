from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Literal, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from apps.pro_api.storage import tenant_store
from services.incrementality.experiments import (
    analyze_experiment_results,
    assess_experiment_power,
    propose_experiment_design,
)
from services.incrementality.models import (
    ExperimentPlan,
    ExperimentPowerAnalysis,
    ExperimentResultAnalysis,
)

router = APIRouter(prefix="/experiments", tags=["Experiments"])


class PowerRequest(BaseModel):
    customer_id: str
    baseline_daily_revenue: Decimal
    baseline_revenue_cv: float
    alpha: float = 0.05
    power: float = 0.80
    treatment_split: float = 0.50
    target_test_days: int = 28
    conversion_lag_days: int = 14


class DesignRequest(BaseModel):
    customer_id: str
    design_type: Literal["PLATFORM_NATIVE_SPLIT", "GEO_BASED_STEP_TEST"] = "GEO_BASED_STEP_TEST"
    test_duration_days: int = 28
    pre_period_days: int = 28
    conversion_lag_days: int = 14
    power_mde_pct: float = 8.5


class AnalyzeRequest(BaseModel):
    test_id: str
    pre_period_start: dt.date
    pre_period_end: dt.date
    test_period_start: dt.date
    test_period_end: dt.date
    treat_pre_revenue: Decimal
    treat_pre_spend: Decimal
    treat_post_revenue: Decimal
    treat_post_spend: Decimal
    ctrl_pre_revenue: Decimal
    ctrl_pre_spend: Decimal
    ctrl_post_revenue: Decimal
    ctrl_post_spend: Decimal
    revenue_daily_stdev: float = 500.0


@router.post("/power", response_model=ExperimentPowerAnalysis)
def calculate_power(req: PowerRequest) -> ExperimentPowerAnalysis:
    return assess_experiment_power(
        customer_id=req.customer_id,
        baseline_daily_revenue=req.baseline_daily_revenue,
        baseline_revenue_cv=req.baseline_revenue_cv,
        alpha=req.alpha,
        power=req.power,
        treatment_split=req.treatment_split,
        target_test_days=req.target_test_days,
        conversion_lag_days=req.conversion_lag_days,
    )


@router.post("/design", response_model=ExperimentPlan)
def generate_design(
    req: DesignRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> ExperimentPlan:
    plan = propose_experiment_design(
        customer_id=req.customer_id,
        design_type=req.design_type,
        test_duration_days=req.test_duration_days,
        pre_period_days=req.pre_period_days,
        conversion_lag_days=req.conversion_lag_days,
        power_mde_pct=req.power_mde_pct,
    )
    ws = tenant_store.get_or_create_workspace(x_workspace_id)
    ws.experiment_plans[plan.plan_id] = plan
    return plan


@router.post("/analyze", response_model=ExperimentResultAnalysis)
def run_analysis(
    req: AnalyzeRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> ExperimentResultAnalysis:
    res = analyze_experiment_results(
        test_id=req.test_id,
        pre_period_start=req.pre_period_start,
        pre_period_end=req.pre_period_end,
        test_period_start=req.test_period_start,
        test_period_end=req.test_period_end,
        treat_pre_revenue=req.treat_pre_revenue,
        treat_pre_spend=req.treat_pre_spend,
        treat_post_revenue=req.treat_post_revenue,
        treat_post_spend=req.treat_post_spend,
        ctrl_pre_revenue=req.ctrl_pre_revenue,
        ctrl_pre_spend=req.ctrl_pre_spend,
        ctrl_post_revenue=req.ctrl_post_revenue,
        ctrl_post_spend=req.ctrl_post_spend,
        revenue_daily_stdev=req.revenue_daily_stdev,
    )
    ws = tenant_store.get_or_create_workspace(x_workspace_id)
    ws.experiment_analyses[res.test_id] = res
    return res
