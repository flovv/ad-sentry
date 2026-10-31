import datetime as dt
from decimal import Decimal
import os
import pytest

from pmax_sentry_core.api import fetch_pmax_delivery, fetch_search_insights
from pmax_sentry_pro._auth import verify_license
from pmax_sentry_pro.reporter import generate_white_label_html_deck
from services.decision_contracts.generator import create_delivery_review_contract
from services.incrementality.economics import calculate_breakeven_hurdle


def test_polar_license_verification_test_key():
    # Test valid agency evaluation key
    res = verify_license(api_key="PMAX_TEST_AGENCY_PRO_KEY_12345")
    assert res["status"] == "granted"
    assert res["tier"] == "agency_pro"
    assert res["accounts_limit"] == 50
    assert res["test_mode"] is True


def test_polar_license_verification_single_pass_key():
    res = verify_license(api_key="PMAX_TEST_SINGLE_PASS_KEY")
    assert res["status"] == "granted"
    assert res["tier"] == "single_pass"
    assert res["accounts_limit"] == 1


def test_polar_license_verification_missing_key_raises():
    # If environment key is empty and no key passed, raises PermissionError
    old_key = os.environ.get("PMAX_API_KEY")
    try:
        if "PMAX_API_KEY" in os.environ:
            del os.environ["PMAX_API_KEY"]
        if "PMAX_LICENSE_KEY" in os.environ:
            del os.environ["PMAX_LICENSE_KEY"]
        with pytest.raises(PermissionError) as exc_info:
            verify_license(api_key=None)
        assert "license key required" in str(exc_info.value)
    finally:
        if old_key is not None:
            os.environ["PMAX_API_KEY"] = old_key


def test_generate_white_label_html_deck():
    delivery_report = fetch_pmax_delivery("1234567890", dt.date(2026, 10, 1), dt.date(2026, 10, 5))
    search_insights = fetch_search_insights("1234567890", dt.date(2026, 10, 1), dt.date(2026, 10, 5))
    hurdle = calculate_breakeven_hurdle(0.35)
    contract = create_delivery_review_contract(delivery_report)

    deck_html = generate_white_label_html_deck(
        delivery_report=delivery_report,
        hurdle=hurdle,
        decision_contract=contract,
        search_insights=search_insights,
        agency_name="Apex Digital Agency",
        client_brand_name="Global Retail Inc",
        primary_color_hex="#2563eb",
    )

    assert "<!DOCTYPE html>" in deck_html
    assert "Apex Digital Agency" in deck_html
    assert "Global Retail Inc" in deck_html
    assert "Break-Even Hurdle (1/μ)" in deck_html
    assert "2.86x" in deck_html
    assert "Account Reconciliation & Coverage Audit" in deck_html
    assert "Search Demand Insight Categories" in deck_html
    assert "Decision Contract" in deck_html
