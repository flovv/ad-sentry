from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from pmax_sentry_core.api import (
    fetch_pmax_delivery,
    fetch_search_insights,
    get_account_info,
    list_pmax_campaigns,
)
from pmax_sentry_core.exporters import (
    export_delivery_report_csv,
    export_delivery_report_json,
    export_search_insight_csv,
    export_search_insight_json,
)
from pmax_sentry_core.mock_client import MockGoogleAdsClient
from pmax_sentry_core.models import (
    CoverageSummary,
    DeliveryReport,
    DeliveryRow,
    SearchInsightRow,
)
from pmax_sentry_core.reconciliation import reconcile_delivery


def test_customer_id_normalization():
    row = DeliveryRow(
        customer_id="123-456-7890",
        campaign_id="101",
        campaign_name="PMax US",
        date=date(2026, 10, 15),
        channel="Google Search",
        uses_product_data=True,
        uses_video=False,
        currency_code="USD",
        cost_micros=10_000_000,
        impressions=1000,
        clicks=50,
        conversions=Decimal("2.5"),
        conversion_value=Decimal("120.00"),
    )
    assert row.customer_id == "1234567890"
    assert row.cost == Decimal("10.0")
    assert row.roas == Decimal("12.0")


def test_invalid_customer_id_raises():
    with pytest.raises(ValidationError):
        DeliveryRow(
            customer_id="abc",
            campaign_id="101",
            campaign_name="PMax",
            date=date(2026, 10, 15),
            channel="Google Search",
            currency_code="USD",
            cost_micros=100,
            impressions=10,
            clicks=1,
            conversions=Decimal("0"),
            conversion_value=Decimal("0"),
        )


def test_reconciliation_complete():
    row = DeliveryRow(
        customer_id="1234567890",
        campaign_id="101",
        campaign_name="PMax US",
        date=date(2026, 10, 15),
        channel="Google Search",
        currency_code="USD",
        cost_micros=1_000_000,
        impressions=100,
        clicks=10,
        conversions=Decimal("1"),
        conversion_value=Decimal("50"),
    )
    # Total is identical to segmented
    cov = reconcile_delivery([row], unsegmented_cost_micros=1_000_000)
    assert cov.status == "COMPLETE"
    assert cov.difference_micros == 0
    assert cov.coverage_ratio == Decimal("1.0")


def test_reconciliation_partial_and_raw_diff_preserved():
    row = DeliveryRow(
        customer_id="1234567890",
        campaign_id="101",
        campaign_name="PMax US",
        date=date(2026, 10, 15),
        channel="Google Search",
        currency_code="USD",
        cost_micros=800_000,
        impressions=100,
        clicks=10,
        conversions=Decimal("1"),
        conversion_value=Decimal("50"),
    )
    # Total is 1,000,000, segmented is 800,000 -> raw_diff = +200,000
    cov = reconcile_delivery([row], unsegmented_cost_micros=1_000_000)
    assert cov.status == "PARTIAL"
    assert cov.difference_micros == 200_000
    assert cov.coverage_ratio == Decimal("0.8000")
    # Check that residual is NOT hidden
    assert "Display" not in " ".join(cov.reasons)
    assert "waste" not in " ".join(cov.reasons)


def test_reconciliation_negative_diff_preserved():
    row = DeliveryRow(
        customer_id="1234567890",
        campaign_id="101",
        campaign_name="PMax US",
        date=date(2026, 10, 15),
        channel="Google Search",
        currency_code="USD",
        cost_micros=1_200_000,
        impressions=100,
        clicks=10,
        conversions=Decimal("1"),
        conversion_value=Decimal("50"),
    )
    # Segmented is 1,200,000, total is 1,000,000 -> raw_diff = -200,000
    cov = reconcile_delivery([row], unsegmented_cost_micros=1_000_000)
    assert cov.status == "PARTIAL"
    assert cov.difference_micros == -200_000
    assert cov.coverage_ratio == Decimal("1.2000")


def test_reconciliation_unavailable():
    # Segmented is empty, unsegmented is 1,000,000
    cov = reconcile_delivery([], unsegmented_cost_micros=1_000_000)
    assert cov.status == "UNAVAILABLE"
    assert cov.difference_micros == 1_000_000


def test_delivery_report_date_validation():
    cov = CoverageSummary(
        status="COMPLETE",
        segmented_cost_micros=0,
        unsegmented_cost_micros=0,
        difference_micros=0,
        coverage_ratio=Decimal("1.0"),
        reasons=[],
    )
    with pytest.raises(ValidationError):
        DeliveryReport(
            schema_version="1.0.0",
            api_version="v26",
            generated_at=datetime.now(timezone.utc),
            customer_id="1234567890",
            currency_code="USD",
            timezone="America/New_York",
            start_date=date(2026, 10, 30),
            end_date=date(2026, 10, 1),
            rows=[],
            coverage=cov,
        )


def test_mock_client_delivery_and_exporters():
    client = MockGoogleAdsClient()
    report = client.build_delivery_report(
        customer_id="1234567890",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 5),
    )
    assert report.customer_id == "1234567890"
    assert report.currency_code == "USD"
    assert report.api_version == "v26"
    assert len(report.rows) > 0
    assert report.coverage.status == "COMPLETE"

    # Test CSV export
    csv_out = export_delivery_report_csv(report)
    assert "Customer ID: 1234567890" in csv_out
    assert "Google Search" in csv_out

    # Test JSON export
    json_out = export_delivery_report_json(report)
    assert '"api_version": "v26"' in json_out


def test_search_insights_no_cost_and_brand_classification():
    client = MockGoogleAdsClient()
    insights = client.build_search_insight_report(
        customer_id="1234567890",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 5),
        brand_dictionary=["acme", "brand"],
    )
    assert insights.api_version == "v26"
    assert len(insights.rows) > 0
    # Confirm no cost attribute on rows
    for r in insights.rows:
        assert not hasattr(r, "cost_micros")
        assert not hasattr(r, "cost")

    assert insights.brand_diagnostic is not None
    assert insights.brand_diagnostic.classifiable_query_share > Decimal("0")
    assert insights.brand_diagnostic.brand_query_share > Decimal("0")

    csv_out = export_search_insight_csv(insights)
    assert "Brand Classifier Version:" in csv_out
    assert "Search Demand Insights Report" in csv_out
