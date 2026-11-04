from datetime import date
from decimal import Decimal
import pytest
from typer.testing import CliRunner

from pmax_sentry_cli.cli import app
from pmax_sentry_core.meta_client import MockMetaAdsClient, fetch_meta_asc_audit
from pmax_sentry_pro.reporter import generate_meta_asc_html_deck

runner = CliRunner()


def test_meta_mock_client_asc_audit():
    client = MockMetaAdsClient()
    report = client.build_asc_audit_report(
        account_id="act_123456789",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 30),
        margin=0.28,
    )

    assert report.account_id == "act_123456789"
    assert report.total_spend == Decimal("50000.00")
    assert report.blended_roas == Decimal("3.30")
    assert report.click_only_roas == Decimal("1.90")

    # Check 1: Audience Network Leakage
    assert report.audience_network_severity == "CRITICAL"
    assert report.audience_network_spend_share == Decimal("0.1000")

    # Check 2: Ghost ROAS
    assert report.attribution_split.view_through_dependency_ratio > Decimal("0.40")
    assert report.attribution_split.ghost_roas_inflation_pct > Decimal("70.0")

    # Check 3: Existing Customer Cap
    assert report.audience_cap_audit.cap_exceeded is True
    assert report.audience_cap_audit.actual_existing_spend_pct > Decimal("15.0")

    # Check 4: Hurdle and Profit
    assert report.hurdle is not None
    assert report.hurdle.breakeven_iroas == Decimal("3.57")
    assert report.net_profit_per_euro_spend is not None
    assert report.net_profit_per_euro_spend < Decimal("0")

    # Recommendations
    assert len(report.recommendations) >= 4


def test_generate_meta_asc_html_deck():
    report = fetch_meta_asc_audit(
        account_id="act_987654321",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 30),
        margin=0.28,
    )
    deck_html = generate_meta_asc_html_deck(
        audit_report=report,
        agency_name="Apex Media",
        client_brand_name="Global Retail",
    )
    assert "<!DOCTYPE html>" in deck_html
    assert "Meta Advantage+ Shopping Audit" in deck_html
    assert "Audience Network" in deck_html
    assert "Ghost ROAS Alert" in deck_html


def test_cli_meta_report():
    result = runner.invoke(
        app,
        [
            "meta",
            "report",
            "--account-id",
            "act_123456789",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-30",
            "--margin",
            "0.28",
            "--format",
            "terminal",
        ],
    )
    assert result.exit_code == 0
    assert "Meta Advantage+ Shopping Campaign (ASC) Audit" in result.stdout
    assert "Ghost ROAS Inflation" in result.stdout
    assert "LEAKAGE" in result.stdout
    assert "BREACHED" in result.stdout
