from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional
import json
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
from pmax_sentry_core.meridian import (
    CANONICAL_PMAX_MERIDIAN_CHANNELS,
    export_meridian_csv,
    export_meridian_pmax,
    generate_meridian_python_snippet,
    generate_meridian_spec,
)
from pmax_sentry_cli.formatting import (
    render_meridian_export_summary,

    render_campaigns_table,
    render_delivery_report,
    render_dry_run_panel,
    render_search_insights_report,
)
from pmax_sentry_cli.license_cmd import app as license_app
from pmax_sentry_cli.meta_cmd import app as meta_app

app = typer.Typer(
    name="ad-audit",
    help="Ad Sentry — Independent Black-Box Audit Suite for Google PMax, Demand Gen & Meta Advantage+.",
    no_args_is_help=True,
)
app.add_typer(license_app, name="license")
app.add_typer(meta_app, name="meta")
console = Console()


def _parse_date(date_str: str) -> dt.date:
    try:
        return dt.date.fromisoformat(date_str.strip())
    except ValueError:
        raise typer.BadParameter(f"Invalid date '{date_str}'. Expected format YYYY-MM-DD.")


@app.command("version")
def version_cmd() -> None:
    """Print ad-audit / pmax-audit version and target Google Ads API version."""
    console.print(f"[bold cyan]ad-audit[/bold cyan] (pmax-audit) v0.1.0 (Google Ads API: [bold green]{PINNED_API_VERSION}[/bold green])")


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
    include_demand_gen: bool = typer.Option(False, "--include-demand-gen", "-dg", help="Include Demand Gen campaigns and run cross-campaign overlap audit"),
    audit_assets: bool = typer.Option(True, "--audit-assets/--no-audit-assets", help="Audit PMax Asset Group creative completeness and video health"),
    audit_feed: bool = typer.Option(True, "--audit-feed/--no-audit-feed", help="Audit Shopping feed and identify non-converting Zombie Products"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Display account dry-run summary without fetching full report"),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to google-ads.yaml config file"),
) -> None:
    """Fetch and reconcile PMax (and optionally Demand Gen) delivery mix, asset groups, and product feed."""
    s_date = _parse_date(start_date)
    e_date = _parse_date(end_date)
    if s_date > e_date:
        console.print(f"[bold red]Error:[/bold red] start-date ({s_date}) cannot be after end-date ({e_date}).")
        raise typer.Exit(code=1)

    try:
        account = get_account_info(customer_id, config_path=config)
        campaigns = list_pmax_campaigns(customer_id, config_path=config, include_demand_gen=include_demand_gen)

        if dry_run:
            render_dry_run_panel(account, campaigns, str(s_date), str(e_date), format)
            return

        report = fetch_pmax_delivery(
            customer_id,
            s_date,
            e_date,
            config_path=config,
            include_demand_gen=include_demand_gen,
            audit_assets=audit_assets,
            audit_feed=audit_feed,
        )

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


@app.command("export-meridian")
def export_meridian_cmd(
    customer_id: str = typer.Option(..., "--customer-id", "-c", help="Google Ads 10-digit customer ID"),
    start_date: str = typer.Option(..., "--start-date", "-s", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end-date", "-e", help="End date (YYYY-MM-DD)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to save Meridian-ready CSV"),
    script_out: Optional[Path] = typer.Option(None, "--script-out", help="Path to save Meridian Python ingestion snippet"),
    freq: str = typer.Option("W-MON", "--freq", "-f", help="Aggregation frequency: W-MON (weekly Monday start), D (daily)"),
    geo: str = typer.Option("national", "--geo", "-g", help="Geographic grain for MMM (default: national)"),
    collapse_discovery: bool = typer.Option(False, "--collapse-discovery", help="Collapse Discover/Gmail into pmax_display"),
    format: str = typer.Option("terminal", "--format", help="Output format: terminal, csv, json"),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to google-ads.yaml config file"),
) -> None:
    """Deconstructs PMax into orthogonal channels and exports dataset for Google Meridian MMM."""
    s_date = _parse_date(start_date)
    e_date = _parse_date(end_date)
    if s_date > e_date:
        console.print(f"[bold red]Error:[/bold red] start-date ({s_date}) cannot be after end-date ({e_date}).")
        raise typer.Exit(code=1)

    try:
        report = fetch_pmax_delivery(
            customer_id,
            s_date,
            e_date,
            config_path=config,
            include_demand_gen=False,
            audit_assets=False,
            audit_feed=False,
        )

        df = export_meridian_pmax(
            report,
            freq=freq,
            geo=geo,
            collapse_discovery_to_display=collapse_discovery,
        )

        # Identify active channels in DataFrame
        channels = [
            c[:-6] for c in df.columns if c.endswith("_spend")
        ]

        fmt = format.lower()
        if fmt == "csv":
            csv_text = export_meridian_csv(
                report,
                freq=freq,
                geo=geo,
                collapse_discovery_to_display=collapse_discovery,
            )
            if output:
                output.write_text(csv_text, encoding="utf-8")
                console.print(f"[green]Meridian CSV saved to {output}[/green]")
            else:
                print(csv_text)
            return

        if fmt == "json":
            payload = {
                "customer_id": customer_id,
                "frequency": freq,
                "geo": geo,
                "channels": channels,
                "records": df.to_dict(orient="records"),
                "spec": generate_meridian_spec(channels=channels),
            }
            json_text = json.dumps(payload, indent=2, default=str)
            if output:
                output.write_text(json_text, encoding="utf-8")
                console.print(f"[green]Meridian JSON saved to {output}[/green]")
            else:
                print(json_text)
            return

        if output:
            csv_text = export_meridian_csv(
                report,
                freq=freq,
                geo=geo,
                collapse_discovery_to_display=collapse_discovery,
            )
            output.write_text(csv_text, encoding="utf-8")

        if script_out:
            csv_name = output.name if output else "meridian_pmax_input.csv"
            snippet = generate_meridian_python_snippet(
                channels=channels,
                csv_filename=csv_name,
            )
            script_out.write_text(snippet, encoding="utf-8")
            console.print(f"[bold green]✓ Meridian Python script saved to:[/bold green] {script_out}")

        render_meridian_export_summary(
            df=df,
            channels=channels,
            freq=freq,
            geo=geo,
            output_path=output,
        )

    except Exception as e:
        console.print(f"[bold red]Error exporting for Meridian:[/bold red] {e}")
        raise typer.Exit(code=1)
