from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from pmax_sentry_core.api import (
    fetch_pmax_delivery,
    fetch_search_insights,
    get_account_info,
    list_pmax_campaigns,
)
from pmax_sentry_core.client import PINNED_API_VERSION
from pmax_sentry_core.exporters import (
    export_delivery_report_csv,
    export_delivery_report_json,
    export_search_insight_csv,
    export_search_insight_json,
)
from pmax_sentry_cli.formatting import (
    render_campaigns_table,
    render_delivery_report,
    render_dry_run_panel,
    render_search_insights_report,
)

app = typer.Typer(
    name="pmax-audit",
    help="Open-source Google Ads Performance Max delivery observability and reconciliation tool.",
    no_args_is_help=True,
)
console = Console()


def _parse_date(date_str: str) -> dt.date:
    try:
        return dt.date.fromisoformat(date_str.strip())
    except ValueError:
        raise typer.BadParameter(f"Invalid date '{date_str}'. Expected format YYYY-MM-DD.")


@app.command("version")
def version_cmd() -> None:
    """Print pmax-audit version and target Google Ads API version."""
    console.print(f"[bold cyan]pmax-audit[/bold cyan] v0.1.0 (Google Ads API: [bold green]{PINNED_API_VERSION}[/bold green])")


@app.command("campaigns")
def campaigns_cmd(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Google Ads 10-digit customer ID"),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to google-ads.yaml config file"),
) -> None:
    """List eligible Performance Max campaigns in the Google Ads account."""
    try:
        account = get_account_info(customer_id, config_path=config)
        campaigns = list_pmax_campaigns(customer_id, config_path=config)
        if not campaigns:
            console.print(f"[yellow]No Performance Max campaigns found for customer {customer_id}.[/yellow]")
            raise typer.Exit(code=0)
        render_campaigns_table(account, campaigns)
    except Exception as e:
        console.print(f"[bold red]Error listing campaigns:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("report")
def report_cmd(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Google Ads 10-digit customer ID"),
    start_date: str = typer.Option(..., "--start-date", "-s", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end-date", "-e", help="End date (YYYY-MM-DD)"),
    format: str = typer.Option("terminal", "--format", "-f", help="Output format: terminal, csv, json, html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="File path to save the output"),
    deck: Optional[Path] = typer.Option(None, "--deck", "-d", help="Export standalone White-Label HTML pitch deck"),
    agency: str = typer.Option("Performance Marketing Agency", "--agency", help="Agency name for white-label deck"),
    brand: str = typer.Option("Client Brand", "--brand", help="Client brand name for white-label deck"),
    margin: Optional[float] = typer.Option(None, "--margin", "-m", help="Contribution margin rate (e.g. 0.35) for break-even hurdle"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Display account dry-run summary without fetching full report"),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to google-ads.yaml config file"),
) -> None:
    """Fetch and reconcile PMax reported delivery mix across channels and formats."""
    s_date = _parse_date(start_date)
    e_date = _parse_date(end_date)
    if s_date > e_date:
        console.print(f"[bold red]Error:[/bold red] start-date ({s_date}) cannot be after end-date ({e_date}).")
        raise typer.Exit(code=1)

    try:
        account = get_account_info(customer_id, config_path=config)
        campaigns = list_pmax_campaigns(customer_id, config_path=config)

        if dry_run:
            render_dry_run_panel(account, campaigns, str(s_date), str(e_date), format)
            return

        report = fetch_pmax_delivery(customer_id, s_date, e_date, config_path=config)

        # Handle White-Label Deck generation
        target_deck_path = deck or (output if format.lower() == "html" else None)
        if target_deck_path:
            from pmax_sentry_pro.reporter import generate_white_label_html_deck
            from services.decision_contracts.generator import create_delivery_review_contract
            from services.incrementality.economics import calculate_breakeven_hurdle

            hurdle_obj = calculate_breakeven_hurdle(margin) if margin else None
            contract_obj = create_delivery_review_contract(report)
            insights_obj = fetch_search_insights(customer_id, s_date, e_date, config_path=config)

            deck_html = generate_white_label_html_deck(
                delivery_report=report,
                hurdle=hurdle_obj,
                decision_contract=contract_obj,
                search_insights=insights_obj,
                agency_name=agency,
                client_brand_name=brand or account.descriptive_name,
            )
            target_deck_path.write_text(deck_html, encoding="utf-8")
            console.print(f"[bold green][OK] Standalone White-Label Audit Deck saved to:[/bold green] {target_deck_path}")
            if not output and format.lower() != "html":
                render_delivery_report(report)
            return

        fmt = format.lower()
        if fmt == "csv":
            csv_data = export_delivery_report_csv(report)
            if output:
                output.write_text(csv_data, encoding="utf-8")
                console.print(f"[green]Report saved to {output}[/green]")
            else:
                print(csv_data)
        elif fmt == "json":
            json_data = export_delivery_report_json(report)
            if output:
                output.write_text(json_data, encoding="utf-8")
                console.print(f"[green]Report saved to {output}[/green]")
            else:
                print(json_data)
        elif fmt in ("terminal", "text"):
            render_delivery_report(report)
            if output:
                output.write_text(export_delivery_report_json(report), encoding="utf-8")
                console.print(f"[green]JSON copy saved to {output}[/green]")
        else:
            console.print(f"[bold red]Unsupported format:[/bold red] {format}. Choose from terminal, csv, json, html.")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]Error running report:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("insights")
def insights_cmd(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Google Ads 10-digit customer ID"),
    start_date: str = typer.Option(..., "--start-date", "-s", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end-date", "-e", help="End date (YYYY-MM-DD)"),
    format: str = typer.Option("terminal", "--format", "-f", help="Output format: terminal, csv, json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="File path to save the output"),
    brand_dictionary: Optional[list[str]] = typer.Option(
        None, "--brand-term", "-b", help="Brand term for query demand classification"
    ),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to google-ads.yaml config file"),
) -> None:
    """Fetch search-demand category insights. Note: strictly reports demand metrics without cost."""
    s_date = _parse_date(start_date)
    e_date = _parse_date(end_date)
    if s_date > e_date:
        console.print(f"[bold red]Error:[/bold red] start-date ({s_date}) cannot be after end-date ({e_date}).")
        raise typer.Exit(code=1)

    try:
        report = fetch_search_insights(
            customer_id, s_date, e_date, config_path=config, brand_dictionary=brand_dictionary
        )

        fmt = format.lower()
        if fmt == "csv":
            csv_data = export_search_insight_csv(report)
            if output:
                output.write_text(csv_data, encoding="utf-8")
                console.print(f"[green]Insights saved to {output}[/green]")
            else:
                print(csv_data)
        elif fmt == "json":
            json_data = export_search_insight_json(report)
            if output:
                output.write_text(json_data, encoding="utf-8")
                console.print(f"[green]Insights saved to {output}[/green]")
            else:
                print(json_data)
        elif fmt in ("terminal", "text"):
            render_search_insights_report(report)
            if output:
                output.write_text(export_search_insight_json(report), encoding="utf-8")
                console.print(f"[green]JSON copy saved to {output}[/green]")
        else:
            console.print(f"[bold red]Unsupported format:[/bold red] {format}. Choose from terminal, csv, json.")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]Error running search insights:[/bold red] {e}")
        raise typer.Exit(code=1)
