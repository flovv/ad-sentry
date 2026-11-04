from __future__ import annotations

import datetime as dt
from decimal import Decimal
import pytest
from typer.testing import CliRunner

from pmax_sentry_cli.cli import app
from pmax_sentry_core.mock_client import MockGoogleAdsClient
from pmax_sentry_core.models import (
    AssetGroupAuditRow,
    AssetGroupHealthReport,
    ProductFeedAuditReport,
    ZombieProductRow,
)
from pmax_sentry_pro.reporter import generate_white_label_html_deck

runner = CliRunner()


def test_mock_client_asset_group_audit() -> None:
    client = MockGoogleAdsClient()
    report = client.query_asset_groups("1234567890")

    assert report.total_asset_groups == 3
    assert report.overall_grade in ("A", "B", "C", "D", "F")
    assert report.missing_vertical_video_count >= 1
    assert len(report.asset_groups) == 3

    # Check individual asset group
    ag_core = next(g for g in report.asset_groups if g.asset_group_id == "ag_101")
    assert ag_core.grade == "A+"
    assert ag_core.has_vertical_video is True
    assert ag_core.score >= 90

    ag_clearance = next(g for g in report.asset_groups if g.asset_group_id == "ag_103")
    assert ag_clearance.grade == "F"
    assert ag_clearance.has_audience_signals is False
    assert ag_clearance.score < 50


def test_mock_client_product_feed_zombie_audit() -> None:
    client = MockGoogleAdsClient()
    report = client.query_product_feed("1234567890", dt.date(2026, 10, 1), dt.date(2026, 10, 31))

    assert report.total_products_audited == 184
    assert report.zombie_products_count == 34
    assert report.zombie_spend == Decimal("2720.00")
    assert report.zombie_spend_share > Decimal(15)  # 19.1%
    assert len(report.top_zombie_products) == 4

    for z in report.top_zombie_products:
        assert z.conversions == Decimal("0.0")
        assert z.cost > Decimal(0)
        assert z.classification == "ZOMBIE"


def test_delivery_report_includes_asset_and_feed_audits() -> None:
    client = MockGoogleAdsClient()
    delivery_report = client.build_delivery_report(
        "1234567890",
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 31),
        audit_assets=True,
        audit_feed=True,
    )

    assert delivery_report.asset_group_audit is not None
    assert delivery_report.asset_group_audit.total_asset_groups == 3
    assert delivery_report.product_feed_audit is not None
    assert delivery_report.product_feed_audit.zombie_products_count == 34


def test_html_deck_renders_asset_and_feed_sections(tmp_path) -> None:
    client = MockGoogleAdsClient()
    delivery_report = client.build_delivery_report(
        "1234567890",
        dt.date(2026, 10, 1),
        dt.date(2026, 10, 31),
    )

    html_content = generate_white_label_html_deck(
        delivery_report=delivery_report,
        agency_name="Audit Pro Media",
        client_brand_name="Test Brand",
    )

    assert "Asset Group Creative Completeness" in html_content
    assert "Core Performance Collection" in html_content
    assert "Missing 9:16 Shorts Video" in html_content
    assert "Zombie Products" in html_content
    assert "SKU-8821" in html_content
    assert "Zombie SKUs" in html_content


def test_cli_report_displays_asset_and_feed_tables() -> None:
    res = runner.invoke(
        app,
        [
            "report",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-31",
            "--format",
            "terminal",
        ],
    )
    assert res.exit_code == 0
    assert "Asset Group Quality & Creative Completeness Grader" in res.output
    assert "Zombie Products" in res.output
    assert "SKU-8821" in res.output
