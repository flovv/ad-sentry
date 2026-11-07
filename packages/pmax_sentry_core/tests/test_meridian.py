from datetime import date
from decimal import Decimal
import pandas as pd
import pytest

from pmax_sentry_core.meridian import (
    CANONICAL_PMAX_MERIDIAN_CHANNELS,
    classify_pmax_channel_for_mmm,
    export_meridian_csv,
    export_meridian_pmax,
    generate_meridian_python_snippet,
    generate_meridian_spec,
)
from pmax_sentry_core.mock_client import MockGoogleAdsClient
from pmax_sentry_core.models import (
    CoverageSummary,
    DeliveryReport,
    DeliveryRow,
)


def _make_sample_row(
    channel: str,
    uses_product_data: bool | None = None,
    uses_video: bool | None = None,
    cost_micros: int = 10_000_000,
    impressions: int = 1000,
    clicks: int = 50,
    conversions: str = "2.0",
    conv_val: str = "100.0",
    date_val: date = date(2026, 10, 1),
) -> DeliveryRow:
    return DeliveryRow(
        customer_id="1234567890",
        campaign_id="101",
        campaign_name="Core PMax",
        date=date_val,
        channel=channel,
        uses_product_data=uses_product_data,
        uses_video=uses_video,
        currency_code="USD",
        cost_micros=cost_micros,
        impressions=impressions,
        clicks=clicks,
        conversions=Decimal(conversions),
        conversion_value=Decimal(conv_val),
    )


def test_classify_pmax_channel_for_mmm():
    # 1. Search with shopping feed
    r1 = _make_sample_row("Google Search", uses_product_data=True)
    assert classify_pmax_channel_for_mmm(r1) == "pmax_shopping"

    # 2. Search text
    r2 = _make_sample_row("Google Search", uses_product_data=False)
    assert classify_pmax_channel_for_mmm(r2) == "pmax_search"

    # 3. Search partners
    r3 = _make_sample_row("Search Partners", uses_product_data=False)
    assert classify_pmax_channel_for_mmm(r3) == "pmax_search"

    # 4. YouTube video
    r4 = _make_sample_row("YouTube", uses_video=True)
    assert classify_pmax_channel_for_mmm(r4) == "pmax_youtube"

    # 5. Display
    r5 = _make_sample_row("Display")
    assert classify_pmax_channel_for_mmm(r5) == "pmax_display"

    # 6. Discover & Gmail
    r6 = _make_sample_row("Discover")
    assert classify_pmax_channel_for_mmm(r6) == "pmax_discovery"
    assert classify_pmax_channel_for_mmm(r6, collapse_discovery_to_display=True) == "pmax_display"


def test_export_meridian_pmax_aggregation():
    client = MockGoogleAdsClient()
    report = client.build_delivery_report("1234567890", date(2026, 10, 1), date(2026, 10, 31))

    # Test weekly W-MON export
    df_weekly = export_meridian_pmax(report, freq="W-MON", geo="national")
    assert isinstance(df_weekly, pd.DataFrame)
    assert not df_weekly.empty
    assert "date" in df_weekly.columns
    assert "geo" in df_weekly.columns
    assert "conversions" in df_weekly.columns
    assert "conversion_value" in df_weekly.columns
    assert "pmax_shopping_spend" in df_weekly.columns
    assert "pmax_shopping_impressions" in df_weekly.columns
    assert "pmax_youtube_spend" in df_weekly.columns

    # Verify all Monday dates
    for d_str in df_weekly["date"]:
        dt = pd.to_datetime(d_str)
        assert dt.day_name() == "Monday"

    # Test total spend reconciliation (within small rounding error)
    expected_spend = sum(float(r.cost) for r in report.rows)
    spend_cols = [c for c in df_weekly.columns if c.endswith("_spend")]
    actual_spend = df_weekly[spend_cols].sum().sum()
    assert abs(actual_spend - expected_spend) < 0.50


def test_export_meridian_pmax_daily():
    client = MockGoogleAdsClient()
    report = client.build_delivery_report("1234567890", date(2026, 10, 1), date(2026, 10, 7))

    df_daily = export_meridian_pmax(report, freq="D", geo="US")
    assert len(df_daily) == 7
    assert all(df_daily["geo"] == "US")


def test_export_meridian_pmax_empty():
    from datetime import datetime, timezone
    report = DeliveryReport(
        customer_id="1234567890",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        currency_code="USD",
        timezone="America/New_York",
        generated_at=datetime.now(timezone.utc),
        rows=[],
        coverage=CoverageSummary(
            status="COMPLETE",
            segmented_cost_micros=0,
            unsegmented_cost_micros=0,
            difference_micros=0,
        ),
    )
    df = export_meridian_pmax(report)
    assert df.empty
    assert "date" in df.columns
    assert "pmax_shopping_spend" in df.columns


def test_generate_meridian_spec_and_snippet():
    spec = generate_meridian_spec()
    assert spec["time_col"] == "date"
    assert spec["geo_col"] == "geo"
    assert "pmax_shopping" in spec["media_channels"]
    assert "pmax_shopping_spend" in spec["media_spend_cols"]
    assert "pmax_shopping_impressions" in spec["media_cols"]

    code = generate_meridian_python_snippet()
    assert "DataFrameInputDataBuilder" in code
    assert "pmax_shopping" in code


def test_export_meridian_csv():
    client = MockGoogleAdsClient()
    report = client.build_delivery_report("1234567890", date(2026, 10, 1), date(2026, 10, 31))

    csv_data = export_meridian_csv(report, freq="W-MON")
    assert "# Ad Sentry PMax Deconstructed Dataset for Google Meridian MMM" in csv_data
    assert "date,geo,conversions" in csv_data
