import datetime as dt
from decimal import Decimal
import pytest

from services.data_ingestion.validator import DataIngestionError, parse_business_outcomes_csv
from services.data_quality.preflight import run_data_quality_preflight
from services.decision_contracts.generator import (
    create_delivery_review_contract,
    create_experiment_result_contract,
    create_observational_diagnostic_contract,
)
from services.incrementality.diagnostic import run_incrementality_diagnostic
from services.incrementality.economics import calculate_breakeven_hurdle, calculate_incremental_net_profit
from services.incrementality.experiments import (
    analyze_experiment_results,
    assess_experiment_power,
    propose_experiment_design,
)
from pmax_sentry_core.api import fetch_pmax_delivery


def generate_sample_csv(num_days: int = 40, flat_spend: bool = False) -> str:
    lines = ["date,total_business_revenue,pmax_cost,pmax_conversion_value,organic_revenue,non_pmax_spend,gross_margin_rate,promo_active,stock_constrained"]
    base_date = dt.date(2026, 9, 1)
    for i in range(num_days):
        d = base_date + dt.timedelta(days=i)
        spend = 500.0 if flat_spend else (400.0 + (i % 7) * 40.0)
        pmax_val = spend * 3.2
        tot_rev = 3000.0 + (spend * 1.8) + ((i % 5) * 50.0)
        org_rev = 1500.0 + (spend * 0.1)
        non_pm = 200.0
        promo = 1 if (i % 10 == 0) else 0
        stock = 0
        lines.append(f"{d},{tot_rev:.2f},{spend:.2f},{pmax_val:.2f},{org_rev:.2f},{non_pm:.2f},0.40,{promo},{stock}")
    return "\n".join(lines)


def test_ingestion_valid_csv():
    csv_data = generate_sample_csv(35)
    dataset = parse_business_outcomes_csv(csv_data, "1234567890", "USD")
    assert dataset.customer_id == "1234567890"
    assert len(dataset.records) == 35
    assert dataset.currency_code == "USD"
    assert dataset.total_revenue > Decimal(0)
    assert dataset.total_pmax_cost > Decimal(0)


def test_ingestion_missing_required_column():
    csv_data = "date,total_business_revenue,pmax_cost\n2026-10-01,1000,200"
    with pytest.raises(DataIngestionError) as exc_info:
        parse_business_outcomes_csv(csv_data, "1234567890", "USD")
    assert "Missing required CSV columns" in str(exc_info.value)


def test_ingestion_negative_value_rejected():
    csv_data = "date,total_business_revenue,pmax_cost,pmax_conversion_value\n2026-10-01,-1000,200,600"
    with pytest.raises(DataIngestionError) as exc_info:
        parse_business_outcomes_csv(csv_data, "1234567890", "USD")
    assert "cannot be negative" in str(exc_info.value)


def test_data_quality_preflight_passed():
    csv_data = generate_sample_csv(45)
    dataset = parse_business_outcomes_csv(csv_data, "1234567890", "USD")
    report = run_data_quality_preflight(dataset, lag_days=14)
    assert report.status == "PASSED"
    assert report.eligible_for_observational is True
    assert report.record_count == 45
    assert report.matured_record_count == 31


def test_data_quality_preflight_insufficient_sample_size():
    csv_data = generate_sample_csv(15)  # only 15 days
    dataset = parse_business_outcomes_csv(csv_data, "1234567890", "USD")
    report = run_data_quality_preflight(dataset, lag_days=14)
    assert report.status == "INSUFFICIENT_DATA"
    assert report.eligible_for_observational is False


def test_data_quality_flat_spend_warning_or_fail():
    csv_data = generate_sample_csv(45, flat_spend=True)
    dataset = parse_business_outcomes_csv(csv_data, "1234567890", "USD")
    report = run_data_quality_preflight(dataset, lag_days=14)
    # Flat spend triggers CV < 0.05 fail
    spend_check = [c for c in report.checks if c.check_name == "spend_variability"][0]
    assert spend_check.status == "FAIL"
    assert report.status == "INSUFFICIENT_DATA"


def test_observational_diagnostic():
    csv_data = generate_sample_csv(45)
    dataset = parse_business_outcomes_csv(csv_data, "1234567890", "USD")
    diag = run_incrementality_diagnostic(dataset, lag_days=14)
    assert diag.status in ("COMPLETED", "LOW_CONFIDENCE")
    assert diag.evidence_class == "OBSERVATIONAL"
    assert diag.modeled_iroas_estimate is not None
    assert diag.modeled_iroas_estimate.point_estimate > Decimal(0)
    assert diag.association_diagnostic is not None
    assert "cannibalization proof" in diag.association_diagnostic.caution


def test_experiment_power_analysis():
    power = assess_experiment_power(
        customer_id="1234567890",
        baseline_daily_revenue=Decimal("5000.00"),
        baseline_revenue_cv=0.12,
        target_test_days=28,
        conversion_lag_days=14,
    )
    assert power.feasibility in ("FEASIBLE", "BORDERLINE")
    assert power.mde_pct > 0.0
    assert power.total_study_duration_days == 70  # 28 pre + 28 test + 14 lag


def test_experiment_design_proposal():
    plan = propose_experiment_design(
        customer_id="1234567890",
        design_type="GEO_BASED_STEP_TEST",
        test_duration_days=28,
    )
    assert plan.design_type == "GEO_BASED_STEP_TEST"
    assert len(plan.treatment_units) > 0
    assert len(plan.control_units) > 0
    assert len(plan.prohibited_campaign_changes) > 0
    assert len(plan.stop_conditions) > 0


def test_experiment_result_analysis():
    res = analyze_experiment_results(
        test_id="test_geo_01",
        pre_period_start=dt.date(2026, 9, 1),
        pre_period_end=dt.date(2026, 9, 28),
        test_period_start=dt.date(2026, 9, 29),
        test_period_end=dt.date(2026, 10, 26),
        treat_pre_revenue=Decimal("100000"),
        treat_pre_spend=Decimal("20000"),
        treat_post_revenue=Decimal("130000"),  # +30,000
        treat_post_spend=Decimal("30000"),    # +10,000
        ctrl_pre_revenue=Decimal("100000"),
        ctrl_pre_spend=Decimal("20000"),
        ctrl_post_revenue=Decimal("110000"),   # +10,000
        ctrl_post_spend=Decimal("20000"),     # +0
    )
    assert res.evidence_class == "EXPERIMENTAL"
    # Incremental revenue = 30,000 - 10,000 = 20,000
    # Incremental spend = 10,000 - 0 = 10,000
    # measured iROAS = 20,000 / 10,000 = 2.00
    assert res.incremental_revenue == Decimal("20000.00")
    assert res.incremental_spend == Decimal("10000.00")
    assert res.measured_iroas.point_estimate == Decimal("2.00")
    assert res.statistically_significant is True


def test_economic_hurdle_and_profit():
    # Margin rate mu = 0.25 (25%) -> breakeven hurdle = 1 / 0.25 = 4.00
    hurdle = calculate_breakeven_hurdle(0.25)
    assert hurdle.breakeven_iroas == Decimal("4.00")
    assert "Break-even iROAS = 1 / mu" in hurdle.formula

    # Profit calculation: 40,000 rev * 0.25 margin - 8,000 spend = 10,000 - 8,000 = +2,000
    profit = calculate_incremental_net_profit(
        incremental_revenue=Decimal("40000"),
        incremental_spend=Decimal("8000"),
        contribution_margin_rate=Decimal("0.25"),
    )
    assert profit == Decimal("2000.00")


def test_decision_contract_generation():
    rep = fetch_pmax_delivery("1234567890", dt.date(2026, 10, 1), dt.date(2026, 10, 5))
    contract = create_delivery_review_contract(rep)
    assert contract.contract_version == "1.0.0"
    assert contract.customer_id == "1234567890"
    assert contract.evidence_class == "REPORTED"
    assert contract.recommendation_type == "REVIEW"
    assert contract.approval_required is True
    # Verify no live mutation fields
    assert not hasattr(contract, "mutate_operations")
    assert not hasattr(contract, "campaign_write_payload")
