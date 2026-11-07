import datetime as dt
import json
import pytest

from pmax_sentry_mcp.server import (
    analyze_completed_experiment_results,
    assess_experiment_readiness,
    calculate_contribution_margin_hurdle,
    fetch_pmax_delivery_report,
    fetch_search_demand_insights,
    generate_decision_contract,
    list_accessible_customers,
    list_pmax_campaigns,
    propose_experiment_design,
    run_incrementality_diagnostic,
    validate_business_outcomes,
    export_meridian_dataset,
)
from tests.test_services import generate_sample_csv


def test_mcp_list_customers():
    customers = list_accessible_customers()
    assert len(customers) > 0
    assert any(c["customer_id"] == "1234567890" for c in customers)


def test_mcp_list_campaigns():
    camps = list_pmax_campaigns("1234567890")
    assert len(camps) > 0
    assert any(c["status"] == "ENABLED" for c in camps)


def test_mcp_delivery_report():
    rep = fetch_pmax_delivery_report("1234567890", "2026-10-01", "2026-10-05")
    assert rep["customer_id"] == "1234567890"
    assert rep["api_version"] == "v26"
    assert len(rep["rows"]) > 0


def test_mcp_search_insights():
    rep = fetch_search_demand_insights("1234567890", "2026-10-01", "2026-10-05", ["acme"])
    assert rep["customer_id"] == "1234567890"
    assert len(rep["rows"]) > 0


def test_mcp_validate_business_outcomes():
    csv_data = generate_sample_csv(35)
    res = validate_business_outcomes("1234567890", csv_data, "USD")
    assert res["preflight_status"] == "PASSED"
    assert res["record_count"] == 35


def test_mcp_incrementality_diagnostic():
    csv_data = generate_sample_csv(40)
    res = run_incrementality_diagnostic("1234567890", csv_data, "USD", conversion_lag_days=14)
    assert res["evidence_class"] == "OBSERVATIONAL"
    assert res["modeled_iroas_estimate"] is not None


def test_mcp_hurdle():
    res = calculate_contribution_margin_hurdle(0.20)
    assert res["breakeven_iroas"] == "5.00"


def test_mcp_experiment_readiness():
    res = assess_experiment_readiness("1234567890", 8000.0, 0.12, 28, 14)
    assert res["feasibility"] in ("FEASIBLE", "BORDERLINE")


def test_mcp_analyze_completed_experiment():
    res = analyze_completed_experiment_results(
        test_id="mcp_test_01",
        pre_period_start="2026-09-01",
        pre_period_end="2026-09-28",
        test_period_start="2026-09-29",
        test_period_end="2026-10-26",
        treat_pre_revenue=50000.0,
        treat_pre_spend=10000.0,
        treat_post_revenue=70000.0,
        treat_post_spend=15000.0,
        ctrl_pre_revenue=50000.0,
        ctrl_pre_spend=10000.0,
        ctrl_post_revenue=55000.0,
        ctrl_post_spend=10000.0,
    )
    assert res["evidence_class"] == "EXPERIMENTAL"
    assert res["measured_iroas"]["point_estimate"] == "3.00"


def test_mcp_propose_design():
    plan = propose_experiment_design("1234567890", "GEO_BASED_STEP_TEST", 28, 28, 14, 8.5)
    assert plan["design_type"] == "GEO_BASED_STEP_TEST"
    assert len(plan["treatment_units"]) > 0


def test_mcp_generate_contract():
    rep = fetch_pmax_delivery_report("1234567890", "2026-10-01", "2026-10-05")
    contract = generate_decision_contract("1234567890", "delivery_review", json.dumps(rep))
    assert contract["contract_version"] == "1.0.0"
    assert contract["recommendation_type"] == "REVIEW"
    assert contract["approval_required"] is True


def test_mcp_export_meridian_dataset():
    res = export_meridian_dataset(
        customer_id="1234567890",
        start_date="2026-10-01",
        end_date="2026-10-31",
        freq="W-MON",
        geo="national",
    )
    assert res["customer_id"] == "1234567890"
    assert res["frequency"] == "W-MON"
    assert res["geo"] == "national"
    assert res["record_count"] > 0
    assert len(res["active_channels"]) > 0
    assert "meridian_spec" in res
    assert "time_col" in res["meridian_spec"]
    assert "python_ingestion_snippet" in res
    assert "DataFrameInputDataBuilder" in res["python_ingestion_snippet"]
