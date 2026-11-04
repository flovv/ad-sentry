import datetime as dt
from decimal import Decimal
import pytest

from apps.pro_api.main import app
from pmax_sentry_pro.client import PMaxSentryProClient
from tests.test_services import generate_sample_csv


@pytest.fixture
def pro_client():
    client = PMaxSentryProClient(app=app, workspace_id="ws_test_tenant")
    yield client
    client.close()


def test_pro_client_health(pro_client):
    h = pro_client.health()
    assert h["status"] == "healthy"
    assert h["service"] == "pmax-sentry-pro"
    assert h["read_only"] == "true"


def test_pro_client_account_connection_and_workspace(pro_client):
    account = pro_client.connect_account("1234567890")
    assert account["customer_id"] == "1234567890"
    assert account["currency_code"] == "USD"

    ws = pro_client.get_workspace()
    assert "1234567890" in ws["accounts"]


def test_pro_client_delivery_report(pro_client):
    rep = pro_client.get_delivery_report(
        customer_id="1234567890",
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 5),
    )
    assert rep.customer_id == "1234567890"
    assert rep.api_version == "v26"
    assert len(rep.rows) > 0
    assert rep.coverage.status == "COMPLETE"


def test_pro_client_search_insights(pro_client):
    rep = pro_client.get_search_insights(
        customer_id="1234567890",
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 5),
        brand_dictionary=["acme"],
    )
    assert rep.customer_id == "1234567890"
    assert len(rep.rows) > 0


def test_pro_client_business_outcomes_flow(pro_client):
    csv_data = generate_sample_csv(40)
    dataset = pro_client.upload_business_outcomes(
        csv_content=csv_data,
        customer_id="1234567890",
        currency_code="USD",
    )
    assert dataset.dataset_id.startswith("ds_")

    preflight = pro_client.run_preflight_check(dataset.dataset_id, conversion_lag_days=14)
    assert preflight.status == "PASSED"
    assert preflight.eligible_for_observational is True

    diag = pro_client.run_incrementality_diagnostic(dataset.dataset_id, conversion_lag_days=14)
    assert diag.evidence_class == "OBSERVATIONAL"
    assert diag.modeled_iroas_estimate is not None


def test_pro_client_experiment_and_economics_flow(pro_client):
    power = pro_client.calculate_power(
        customer_id="1234567890",
        baseline_daily_revenue=Decimal("10000"),
        baseline_revenue_cv=0.10,
        target_test_days=28,
        conversion_lag_days=14,
    )
    assert power.feasibility == "FEASIBLE"

    plan = pro_client.generate_experiment_design(
        customer_id="1234567890",
        design_type="GEO_BASED_STEP_TEST",
        test_duration_days=28,
    )
    assert len(plan.treatment_units) > 0

    analysis = pro_client.analyze_experiment(
        test_id="test_geo_did_01",
        pre_period_start=dt.date(2026, 9, 1),
        pre_period_end=dt.date(2026, 9, 28),
        test_period_start=dt.date(2026, 9, 29),
        test_period_end=dt.date(2026, 10, 26),
        treat_pre_revenue=Decimal("50000"),
        treat_pre_spend=Decimal("10000"),
        treat_post_revenue=Decimal("70000"),
        treat_post_spend=Decimal("15000"),
        ctrl_pre_revenue=Decimal("50000"),
        ctrl_pre_spend=Decimal("10000"),
        ctrl_post_revenue=Decimal("55000"),
        ctrl_post_spend=Decimal("10000"),
    )
    assert analysis.evidence_class == "EXPERIMENTAL"
    assert analysis.measured_iroas.point_estimate == Decimal("3.00")

    hurdle = pro_client.calculate_breakeven_hurdle(Decimal("0.33"))
    assert hurdle.breakeven_iroas == Decimal("3.03")


def test_pro_client_contract_and_disconnection(pro_client):
    rep = pro_client.get_delivery_report(
        customer_id="1234567890",
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 5),
    )
    contract = pro_client.create_contract_from_delivery(rep)
    assert contract.contract_id.startswith("cntr_")
    assert contract.evidence_class == "REPORTED"

    # Fetch contract back
    fetched = pro_client.get_contract(contract.contract_id)
    assert fetched.contract_id == contract.contract_id

    # Disconnect account
    disc = pro_client.disconnect_account("1234567890")
    assert disc["status"] == "DISCONNECTED"

    # Delete workspace
    del_res = pro_client.delete_workspace_data()
    assert del_res["status"] == "DELETED"
