from __future__ import annotations

import datetime as dt
from decimal import Decimal
import json
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP

from pmax_sentry_core.api import (
    fetch_pmax_delivery,
    fetch_search_insights,
    get_account_info,
    list_pmax_campaigns as core_list_campaigns,
)
from pmax_sentry_core.models import DeliveryReport
from services.data_ingestion.validator import parse_business_outcomes_csv
from services.data_quality.preflight import run_data_quality_preflight
from services.decision_contracts.generator import (
    create_delivery_review_contract,
    create_experiment_result_contract,
    create_observational_diagnostic_contract,
)
from services.incrementality.diagnostic import run_incrementality_diagnostic as run_diag
from services.incrementality.economics import calculate_breakeven_hurdle
from services.incrementality.experiments import (
    analyze_experiment_results as analyze_exp,
    assess_experiment_power,
    propose_experiment_design as propose_design,
)

mcp = FastMCP("PMax Sentry Measurement Server")


@mcp.tool()
def list_accessible_customers() -> list[dict[str, Any]]:
    """
    List accessible Google Ads customer accounts with their descriptive name, currency, and timezone.
    Read-only operation.
    """
    # Returns configured accounts or mock accounts in sandbox
    cids = ["1234567890", "2345678901", "3456789012"]
    res = []
    for cid in cids:
        acc = get_account_info(cid)
        res.append(
            {
                "customer_id": acc.customer_id,
                "name": acc.descriptive_name,
                "currency": acc.currency_code,
                "timezone": acc.time_zone,
            }
        )
    return res


@mcp.tool()
def list_pmax_campaigns(customer_id: str) -> list[dict[str, Any]]:
    """
    List eligible Performance Max campaigns in a Google Ads customer account.
    Returns campaign IDs, names, status (ENABLED, PAUSED), bidding strategy, and target ROAS.
    """
    camps = core_list_campaigns(customer_id)
    return [c.model_dump() for c in camps]


@mcp.tool()
def fetch_pmax_delivery_report(customer_id: str, start_date: str, end_date: str) -> dict[str, Any]:
    """
    Fetch descriptive Performance Max delivery report broken down by channel and format flags.
    Includes campaign totals reconciliation check and coverage status (COMPLETE, PARTIAL, UNAVAILABLE).
    Date format: YYYY-MM-DD.
    """
    s = dt.date.fromisoformat(start_date)
    e = dt.date.fromisoformat(end_date)
    rep = fetch_pmax_delivery(customer_id, s, e)
    return rep.model_dump(mode="json")


@mcp.tool()
def fetch_search_demand_insights(
    customer_id: str,
    start_date: str,
    end_date: str,
    brand_dictionary: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Fetch search-demand categories for PMax campaigns.
    Important: strictly reports clicks, conversions, impressions, and search volume.
    NEVER returns cost or spend by category.
    """
    s = dt.date.fromisoformat(start_date)
    e = dt.date.fromisoformat(end_date)
    rep = fetch_search_insights(customer_id, s, e, brand_dictionary=brand_dictionary)
    return rep.model_dump(mode="json")


@mcp.tool()
def validate_business_outcomes(
    customer_id: str,
    csv_content: str,
    currency_code: str,
    timezone: str = "UTC",
) -> dict[str, Any]:
    """
    Validate uploaded daily business outcome data (total revenue, PMax spend, conversions, controls).
    Runs preflight data quality checks (minimum duration, date gaps, lag maturation, spend variability).
    """
    ds = parse_business_outcomes_csv(
        csv_content=csv_content,
        customer_id=customer_id,
        currency_code=currency_code,
        timezone=timezone,
    )
    pf = run_data_quality_preflight(ds)
    return {
        "dataset_id": ds.dataset_id,
        "record_count": len(ds.records),
        "start_date": str(ds.start_date),
        "end_date": str(ds.end_date),
        "preflight_status": pf.status,
        "eligible_for_observational": pf.eligible_for_observational,
        "eligible_for_experiment": pf.eligible_for_experiment,
        "checks": [c.model_dump() for c in pf.checks],
        "reasons": pf.reasons,
    }


@mcp.tool()
def run_incrementality_diagnostic(
    customer_id: str,
    csv_content: str,
    currency_code: str,
    conversion_lag_days: int = 14,
) -> dict[str, Any]:
    """
    Execute an observational incrementality diagnostic on historical business outcomes.
    Returns modeled iROAS estimate with 95% confidence intervals, OLS diagnostics, and organic sensitivity.
    Declared Evidence Class: OBSERVATIONAL. Does NOT claim causal proof or cannibalization.
    """
    ds = parse_business_outcomes_csv(
        csv_content=csv_content,
        customer_id=customer_id,
        currency_code=currency_code,
    )
    diag = run_diag(ds, lag_days=conversion_lag_days)
    return diag.model_dump(mode="json")


@mcp.tool()
def calculate_contribution_margin_hurdle(contribution_margin_rate: float) -> dict[str, Any]:
    """
    Calculate the advertiser's economic break-even incremental ROAS hurdle: 1 / mu.
    Also explains marginal spend stopping conditions.
    """
    res = calculate_breakeven_hurdle(contribution_margin_rate)
    return res.model_dump(mode="json")


@mcp.tool()
def assess_experiment_readiness(
    customer_id: str,
    baseline_daily_revenue: float,
    baseline_revenue_cv: float,
    test_days: int = 28,
    conversion_lag_days: int = 14,
) -> dict[str, Any]:
    """
    Assess statistical power and minimum detectable effect (MDE) for a prospective PMax incrementality test.
    Calculates required test duration and feasibility dynamically based on baseline revenue variance and lag.
    """
    res = assess_experiment_power(
        customer_id=customer_id,
        baseline_daily_revenue=Decimal(str(baseline_daily_revenue)),
        baseline_revenue_cv=baseline_revenue_cv,
        target_test_days=test_days,
        conversion_lag_days=conversion_lag_days,
    )
    return res.model_dump(mode="json")


@mcp.tool()
def analyze_completed_experiment_results(
    test_id: str,
    pre_period_start: str,
    pre_period_end: str,
    test_period_start: str,
    test_period_end: str,
    treat_pre_revenue: float,
    treat_pre_spend: float,
    treat_post_revenue: float,
    treat_post_spend: float,
    ctrl_pre_revenue: float,
    ctrl_pre_spend: float,
    ctrl_post_revenue: float,
    ctrl_post_spend: float,
) -> dict[str, Any]:
    """
    Analyze causal Difference-in-Differences (DiD) outcomes for a completed PMax incrementality experiment.
    Declared Evidence Class: EXPERIMENTAL. Returns measured iROAS, 95% confidence interval, and p-value.
    """
    res = analyze_exp(
        test_id=test_id,
        pre_period_start=dt.date.fromisoformat(pre_period_start),
        pre_period_end=dt.date.fromisoformat(pre_period_end),
        test_period_start=dt.date.fromisoformat(test_period_start),
        test_period_end=dt.date.fromisoformat(test_period_end),
        treat_pre_revenue=Decimal(str(treat_pre_revenue)),
        treat_pre_spend=Decimal(str(treat_pre_spend)),
        treat_post_revenue=Decimal(str(treat_post_revenue)),
        treat_post_spend=Decimal(str(treat_post_spend)),
        ctrl_pre_revenue=Decimal(str(ctrl_pre_revenue)),
        ctrl_pre_spend=Decimal(str(ctrl_pre_spend)),
        ctrl_post_revenue=Decimal(str(ctrl_post_revenue)),
        ctrl_post_spend=Decimal(str(ctrl_post_spend)),
    )
    return res.model_dump(mode="json")


@mcp.tool()
def propose_experiment_design(
    customer_id: str,
    design_type: str = "GEO_BASED_STEP_TEST",
    test_duration_days: int = 28,
    pre_period_days: int = 28,
    conversion_lag_days: int = 14,
    power_mde_pct: float = 8.5,
) -> dict[str, Any]:
    """
    Generate an experiment protocol plan including treatment/control units, allowable campaign changes,
    contamination risks, stop conditions, and interpretation limits.
    """
    plan = propose_design(
        customer_id=customer_id,
        design_type=design_type,  # type: ignore
        test_duration_days=test_duration_days,
        pre_period_days=pre_period_days,
        conversion_lag_days=conversion_lag_days,
        power_mde_pct=power_mde_pct,
    )
    return plan.model_dump(mode="json")


@mcp.tool()
def generate_decision_contract(
    customer_id: str,
    contract_type: str,
    payload_json: str,
) -> dict[str, Any]:
    """
    Generate a formal JSON decision contract object conforming to Section 8.
    contract_type: 'delivery_review', 'diagnostic', or 'experiment'.
    Requires explicit human approval; cannot execute live mutations.
    """
    data = json.loads(payload_json)
    if contract_type == "delivery_review":
        rep = DeliveryReport.model_validate(data)
        contract = create_delivery_review_contract(rep)
    elif contract_type == "diagnostic":
        diag = run_diag(data)  # or passed object
        contract = create_observational_diagnostic_contract(customer_id, diag)
    elif contract_type == "experiment":
        analysis = analyze_exp(**data)
        contract = create_experiment_result_contract(customer_id, analysis)
    else:
        raise ValueError(f"Unknown contract_type '{contract_type}'")
    return contract.model_dump(mode="json")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
