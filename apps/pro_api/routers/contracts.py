from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from apps.pro_api.storage import tenant_store
from pmax_sentry_core.models import DeliveryReport
from services.decision_contracts.generator import (
    create_delivery_review_contract,
    create_experiment_result_contract,
    create_observational_diagnostic_contract,
)
from services.decision_contracts.models import DecisionContract
from services.incrementality.models import (
    EconomicHurdleResult,
    ExperimentPlan,
    ExperimentPowerAnalysis,
    ExperimentResultAnalysis,
    ObservationalDiagnosticResult,
)

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post("/from-delivery", response_model=DecisionContract)
def contract_from_delivery(
    report: DeliveryReport,
    x_workspace_id: str = Header(default="default_ws"),
) -> DecisionContract:
    contract = create_delivery_review_contract(report)
    tenant_store.store_contract(x_workspace_id, contract)
    return contract


class DiagnosticContractRequest(BaseModel):
    customer_id: str
    diagnostic: ObservationalDiagnosticResult
    hurdle: Optional[EconomicHurdleResult] = None
    power: Optional[ExperimentPowerAnalysis] = None
    experiment_plan: Optional[ExperimentPlan] = None


@router.post("/from-diagnostic", response_model=DecisionContract)
def contract_from_diagnostic(
    req: DiagnosticContractRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> DecisionContract:
    contract = create_observational_diagnostic_contract(
        customer_id=req.customer_id,
        diagnostic=req.diagnostic,
        hurdle=req.hurdle,
        power=req.power,
        experiment_plan=req.experiment_plan,
    )
    tenant_store.store_contract(x_workspace_id, contract)
    return contract


class ExperimentContractRequest(BaseModel):
    customer_id: str
    analysis: ExperimentResultAnalysis
    hurdle: Optional[EconomicHurdleResult] = None


@router.post("/from-experiment", response_model=DecisionContract)
def contract_from_experiment(
    req: ExperimentContractRequest,
    x_workspace_id: str = Header(default="default_ws"),
) -> DecisionContract:
    contract = create_experiment_result_contract(
        customer_id=req.customer_id,
        analysis=req.analysis,
        hurdle=req.hurdle,
    )
    tenant_store.store_contract(x_workspace_id, contract)
    return contract


@router.get("/{contract_id}", response_model=DecisionContract)
def get_contract(
    contract_id: str,
    x_workspace_id: str = Header(default="default_ws"),
) -> DecisionContract:
    contract = tenant_store.get_contract(x_workspace_id, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Decision contract not found")
    return contract
