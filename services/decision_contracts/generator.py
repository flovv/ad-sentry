from __future__ import annotations

import datetime as dt
from decimal import Decimal
import uuid
from typing import Any, Optional

from pmax_sentry_core.models import DeliveryReport, EvidenceClass
from services.decision_contracts.models import DecisionContract
from services.incrementality.models import (
    EconomicHurdleResult,
    ExperimentPlan,
    ExperimentPowerAnalysis,
    ExperimentResultAnalysis,
    ObservationalDiagnosticResult,
)


def create_delivery_review_contract(report: DeliveryReport) -> DecisionContract:
    """Creates a decision contract from a descriptive PMax delivery report."""
    contract_id = f"cntr_{uuid.uuid4().hex[:12]}"
    valid_until = dt.date.today() + dt.timedelta(days=14)

    campaign_ids = list({r.campaign_id for r in report.rows})

    metrics = {
        "currency": report.currency_code,
        "total_cost": float(report.total_cost),
        "total_conversions": float(report.total_conversions),
        "total_conversion_value": float(report.total_conversion_value),
        "platform_reported_roas": float(report.reported_roas) if report.reported_roas else None,
        "reconciliation_status": report.coverage.status,
        "coverage_ratio": float(report.coverage.coverage_ratio) if report.coverage.coverage_ratio else None,
        "difference_micros": report.coverage.difference_micros,
    }

    return DecisionContract(
        contract_version="1.0.0",
        contract_id=contract_id,
        customer_id=report.customer_id,
        campaign_ids=campaign_ids,
        date_range=(report.start_date, report.end_date),
        timezone=report.timezone,
        evidence_class=EvidenceClass.REPORTED,
        claim="Descriptive delivery mix and account reconciliation summary across channel and format dimensions.",
        evidence_references=[
            f"Google Ads API {report.api_version} campaign resource query",
            f"Unsegmented campaign total vs segmented reporting reconciliation check",
        ],
        reported_metrics=metrics,
        assumptions_and_limitations=[
            "Data is platform-reported delivery only; does not infer incrementality, cannibalization, or waste.",
            "Attributed conversion values depend on platform attribution models and conversion lag maturation.",
        ],
        recommendation_type="REVIEW",
        approval_required=True,
        valid_until=valid_until,
        next_review_date=valid_until,
    )


def create_observational_diagnostic_contract(
    customer_id: str,
    diagnostic: ObservationalDiagnosticResult,
    hurdle: Optional[EconomicHurdleResult] = None,
    power: Optional[ExperimentPowerAnalysis] = None,
    experiment_plan: Optional[ExperimentPlan] = None,
) -> DecisionContract:
    """Creates a decision contract from an observational diagnostic assessment."""
    contract_id = f"cntr_{uuid.uuid4().hex[:12]}"
    valid_until = dt.date.today() + dt.timedelta(days=21)

    model_diagnostics = {
        "model_version": diagnostic.model_version,
        "r_squared": diagnostic.r_squared,
        "p_value": diagnostic.p_value,
        "controls_included": diagnostic.controls_included,
        "omitted_controls": diagnostic.omitted_controls,
    }
    if diagnostic.association_diagnostic:
        model_diagnostics["association_diagnostic"] = {
            "metric": diagnostic.association_diagnostic.metric_name,
            "coefficient": float(diagnostic.association_diagnostic.coefficient),
            "p_value": diagnostic.association_diagnostic.p_value,
            "interpretation": diagnostic.association_diagnostic.interpretation,
            "caution": diagnostic.association_diagnostic.caution,
        }

    rec_type = "EXPERIMENT" if power and power.feasibility in ("FEASIBLE", "BORDERLINE") else "SCENARIO"

    return DecisionContract(
        contract_version="1.0.0",
        contract_id=contract_id,
        customer_id=customer_id,
        campaign_ids=["ALL_PMAX"],
        date_range=diagnostic.matured_date_window,
        timezone="UTC",
        evidence_class=EvidenceClass.OBSERVATIONAL,
        claim="Historical observational incrementality diagnostic and association analysis.",
        evidence_references=[
            f"Dataset: {diagnostic.dataset_id}",
            f"Model version: {diagnostic.model_version}",
        ],
        reported_metrics={
            "platform_reported_roas": float(diagnostic.platform_reported_roas),
            "diagnostic_status": diagnostic.status,
        },
        estimate_and_uncertainty_interval=diagnostic.modeled_iroas_estimate,
        model_version_and_diagnostics=model_diagnostics,
        estimand_and_outcome_definition="Observational sensitivity of total business revenue to PMax ad spend",
        experiment_design=experiment_plan,
        power_mde_and_lag_treatment=power.model_dump() if power else None,
        contribution_margin_and_breakeven_hurdle=hurdle,
        assumptions_and_limitations=diagnostic.assumptions + diagnostic.limitations,
        recommendation_type=rec_type,
        approval_required=True,
        valid_until=valid_until,
        next_review_date=valid_until,
    )


def create_experiment_result_contract(
    customer_id: str,
    analysis: ExperimentResultAnalysis,
    hurdle: Optional[EconomicHurdleResult] = None,
) -> DecisionContract:
    """Creates a decision contract from a completed causal incrementality experiment."""
    contract_id = f"cntr_{uuid.uuid4().hex[:12]}"
    valid_until = dt.date.today() + dt.timedelta(days=30)

    return DecisionContract(
        contract_version="1.0.0",
        contract_id=contract_id,
        customer_id=customer_id,
        campaign_ids=["EXPERIMENT_ARMS"],
        date_range=analysis.test_period,
        timezone="UTC",
        evidence_class=EvidenceClass.EXPERIMENTAL,
        claim=f"Causal incrementality measurement via {analysis.analysis_method}.",
        evidence_references=[
            f"Experiment Test ID: {analysis.test_id}",
            f"Analysis method: {analysis.analysis_method}",
            f"Pre-period: {analysis.pre_period[0]} to {analysis.pre_period[1]}",
            f"Test-period: {analysis.test_period[0]} to {analysis.test_period[1]}",
        ],
        reported_metrics={
            "incremental_revenue": float(analysis.incremental_revenue),
            "incremental_spend": float(analysis.incremental_spend),
            "p_value": analysis.p_value,
            "statistically_significant": analysis.statistically_significant,
        },
        estimate_and_uncertainty_interval=analysis.measured_iroas,
        estimand_and_outcome_definition="Causal lift in total business revenue per unit incremental PMax spend",
        contribution_margin_and_breakeven_hurdle=hurdle,
        assumptions_and_limitations=analysis.assumptions,
        recommendation_type="SCENARIO" if analysis.statistically_significant else "REVIEW",
        approval_required=True,
        valid_until=valid_until,
        next_review_date=valid_until,
    )
