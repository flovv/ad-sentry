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



def test_cli_export_meridian_terminal():
    result = runner.invoke(
        app,
        [
            "export-meridian",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-31",
            "--freq",
            "W-MON",
            "--format",
            "terminal",
        ],
    )
    assert result.exit_code == 0
    assert "Deconstructed PMax Media Mix Channels" in result.stdout
    assert "Google Meridian Ingestion Ready" in result.stdout
    assert "pmax_shop" in result.stdout or "pmax_sear" in result.stdout


def test_cli_export_meridian_files(tmp_path):
    csv_file = tmp_path / "meridian_pmax.csv"
    py_file = tmp_path / "meridian_spec.py"

    result = runner.invoke(
        app,
        [
            "export-meridian",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-31",
            "--output",
            str(csv_file),
            "--script-out",
            str(py_file),
            "--format",
            "terminal",
        ],
    )
    assert result.exit_code == 0
    assert csv_file.exists()
    assert py_file.exists()

    csv_text = csv_file.read_text(encoding="utf-8")
    assert "date,geo,conversions" in csv_text
    assert "pmax_shopping_spend" in csv_text

    py_text = py_file.read_text(encoding="utf-8")
    assert "DataFrameInputDataBuilder" in py_text
    assert "media_cols" in py_text


def test_cli_export_meridian_json():
    result = runner.invoke(
        app,
        [
            "export-meridian",
            "--customer-id",
            "1234567890",
            "--start-date",
            "2026-10-01",
            "--end-date",
            "2026-10-15",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["customer_id"] == "1234567890"
    assert data["frequency"] == "W-MON"
    assert len(data["records"]) > 0
    assert "spec" in data
    assert "media_spend_cols" in data["spec"]
