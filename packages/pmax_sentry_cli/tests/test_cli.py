import json
from typer.testing import CliRunner
from pmax_sentry_cli.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "ad-audit" in result.stdout or "pmax-audit" in result.stdout
    assert "v0.1.0" in result.stdout
    assert "v26" in result.stdout


def test_cli_campaigns():
    result = runner.invoke(app, ["campaigns", "--customer-id", "1234567890"])
    assert result.exit_code == 0
    assert "Performance Max Campaigns" in result.stdout
    assert "10001" in result.stdout
    assert "ENABLED" in result.stdout


def test_cli_report_dry_run():
    result = runner.invoke(
        app,
        [
            "report",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-30",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Dry-Run Preview" in result.stdout
    assert "1234567890" in result.stdout
    assert "USD" in result.stdout


def test_cli_report_csv():
    result = runner.invoke(
        app,
        [
            "report",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-05",
            "--format",
            "csv",
        ],
    )
    assert result.exit_code == 0
    assert "Customer ID: 1234567890" in result.stdout
    assert "Google Search" in result.stdout


def test_cli_report_json():
    result = runner.invoke(
        app,
        [
            "report",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-05",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["customer_id"] == "1234567890"
    assert data["api_version"] == "v26"
    assert data["coverage"]["status"] == "COMPLETE"


def test_cli_insights_json():
    result = runner.invoke(
        app,
        [
            "insights",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-05",
            "--format",
            "json",
            "-b",
            "acme",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["customer_id"] == "1234567890"
    assert len(data["rows"]) > 0
    assert "brand_diagnostic" in data


def test_cli_invalid_date_order():
    result = runner.invoke(
        app,
        [
            "report",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-30",
            "--end-date",
            "2026-10-01",
        ],
    )
    assert result.exit_code != 0
    assert "cannot be after" in result.stdout


def test_cli_report_include_demand_gen():
    result = runner.invoke(
        app,
        [
            "report",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-05",
            "--include-demand-gen",
            "--format",
            "terminal",
        ],
    )
    assert result.exit_code == 0
    assert "Cross-Campaign Overlap & Inventory Collision" in result.stdout
    assert "COLLISION" in result.stdout
    assert "Demand Gen View-Through Share" in result.stdout

