from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pmax_sentry_core.meta_client import fetch_meta_asc_audit
from pmax_sentry_core.meta_models import MetaAscAuditReport
from pmax_sentry_pro.reporter import generate_meta_asc_html_deck

app = typer.Typer(name="meta", help="Audit Meta Advantage+ Shopping Campaigns (ASC).")
console = Console()


def _parse_date(d_str: str) -> dt.date:
    try:
        return dt.date.fromisoformat(d_str)
    except ValueError:
        console.print(f"[bold red]Invalid date format:[/bold red] '{d_str}'. Use YYYY-MM-DD.")
        raise typer.Exit(code=1)


@app.command("report")
def meta_report_cmd(
    account_id: str = typer.Option(..., "--account-id", "-a", help="Meta Ad Account ID (e.g. act_123456789)"),
    start_date: str = typer.Option(..., "--start-date", "-s", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end-date", "-e", help="End date (YYYY-MM-DD)"),
    margin: Optional[float] = typer.Option(None, "--margin", "-m", help="Contribution margin rate (e.g. 0.28) for break-even hurdle"),
    format: str = typer.Option("terminal", "--format", "-f", help="Output format: terminal, json, html"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="File path to save the output"),
    deck: Optional[Path] = typer.Option(None, "--deck", "-d", help="Export standalone White-Label HTML pitch deck"),
    agency: str = typer.Option("Performance Marketing Agency", "--agency", help="Agency name for white-label deck"),
    brand: str = typer.Option("Client Brand", "--brand", help="Client brand name for white-label deck"),
) -> None:
    """Audit Meta Advantage+ (ASC) Placements, 1-Day View-Through Ghost ROAS, and Audience Cap compliance."""
    s_date = _parse_date(start_date)
    e_date = _parse_date(end_date)
    if s_date > e_date:
        console.print(f"[bold red]Error:[/bold red] start-date ({s_date}) cannot be after end-date ({e_date}).")
        raise typer.Exit(code=1)

    try:
        report = fetch_meta_asc_audit(account_id, s_date, e_date, margin=margin)

        # Handle Deck generation
        target_deck_path = deck or (output if format.lower() == "html" else None)
        if target_deck_path:
            deck_html = generate_meta_asc_html_deck(
                audit_report=report,
                agency_name=agency,
                client_brand_name=brand,
            )
            target_deck_path.write_text(deck_html, encoding="utf-8")
            console.print(f"[bold green][OK] Standalone Meta ASC Audit Deck saved to:[/bold green] {target_deck_path}")
            if not output and format.lower() != "html":
                render_meta_report(report)
            return

        fmt = format.lower()
        if fmt == "json":
            json_str = report.model_dump_json(indent=2)
            if output:
                output.write_text(json_str, encoding="utf-8")
                console.print(f"[green]Report saved to {output}[/green]")
            else:
                print(json_str)
        elif fmt in ("terminal", "text"):
            render_meta_report(report)
            if output:
                output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
                console.print(f"[green]JSON copy saved to {output}[/green]")
        else:
            console.print(f"[bold red]Unsupported format:[/bold red] {format}. Choose terminal, json, or html.")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]Error running Meta audit:[/bold red] {e}")
        raise typer.Exit(code=1)


def render_meta_report(report: MetaAscAuditReport) -> None:
    # 1. Summary Header
    summary_text = (
        f"[bold]Account:[/bold] {report.account_id} ({report.account_name})\n"
        f"[bold]Window:[/bold] {report.start_date} to {report.end_date} | [bold]Currency:[/bold] {report.currency_code}\n"
        f"[bold]Total Spend:[/bold] {report.currency_code} {report.total_spend:,.2f} | "
        f"[bold]Attributed Value:[/bold] {report.currency_code} {report.total_conversion_value:,.2f}\n"
        f"[bold]Reported Blended ROAS:[/bold] [cyan]{report.blended_roas:.2f}x[/cyan] (7d-Click + 1d-View)\n"
        f"[bold]De-Vested Click-Only ROAS:[/bold] [bold red]{report.click_only_roas:.2f}x[/bold red] (excludes passive views)"
    )
    if report.hurdle:
        summary_text += f"\n[bold]Break-Even Hurdle (1/mu):[/bold] [magenta]{report.hurdle.breakeven_iroas:.2f}x[/magenta] (Target Margin: {report.hurdle.contribution_margin_rate:.1%})"
        if report.net_profit_per_euro_spend is not None:
            profit_style = "bold green" if report.net_profit_per_euro_spend >= 0 else "bold red"
            summary_text += f"\n[bold]Net Profit per Ad Euro:[/bold] [{profit_style}]{report.net_profit_per_euro_spend:+,.2f} EUR[/]"

    console.print(Panel(summary_text, title="[bold]Meta Advantage+ Shopping Campaign (ASC) Audit[/bold]", border_style="cyan"))

    # 2. Ghost ROAS Alert
    split = report.attribution_split
    alert_text = (
        f"[bold]Ghost ROAS Inflation:[/bold] [bold red]+{split.ghost_roas_inflation_pct:.1f}%[/bold red] inflation from 1-day view attribution.\n"
        f"- Total Conversions: {split.total_reported_conversions:,.1f}\n"
        f"- 7-Day Click Conversions: {split.click_7d_conversions:,.1f} ({report.currency_code} {split.click_7d_value:,.2f})\n"
        f"- 1-Day View-Through Conversions: {split.view_1d_conversions:,.1f} ({report.currency_code} {split.view_1d_value:,.2f})\n"
        f"- [bold]View-Through Dependency Ratio:[/bold] [bold red]{split.view_through_dependency_ratio:.1%}[/bold red] of conversions had zero ad clicks."
    )
    console.print(Panel(alert_text, title="[bold]Check 2: Attribution De-Construction (Ghost ROAS)[/bold]", border_style="red"))

    # 3. Placement Breakdown
    table = Table(title="Check 1: Placement & Surface Breakdown (Audience Network Leakage)", header_style="bold cyan")
    table.add_column("Publisher Platform", style="bold white")
    table.add_column("Position")
    table.add_column("Spend", justify="right", style="yellow")
    table.add_column("Share", justify="right")
    table.add_column("Clicks", justify="right")
    table.add_column("ROAS", justify="right", style="bold green")
    table.add_column("Status", justify="center")

    for p in report.placement_rows:
        share = (p.spend / report.total_spend * 100) if report.total_spend > 0 else 0
        roas_str = f"{p.roas:.2f}x" if p.roas else "-"
        status = "[bold red]LEAKAGE[/bold red]" if p.publisher_platform == "audience_network" and p.spend > 0 else "[green]OK[/green]"
        table.add_row(
            p.publisher_platform.title(),
            p.platform_position.replace("_", " ").title(),
            f"{report.currency_code} {p.spend:,.2f}",
            f"{share:.1f}%",
            f"{p.clicks:,}",
            roas_str,
            status,
        )
    console.print(table)

    # 4. Audience Cap Audit
    cap = report.audience_cap_audit
    cap_color = "red" if cap.cap_exceeded else "green"
    cap_text = (
        f"[bold]Configured Existing Customer Cap:[/bold] {cap.configured_cap_pct:.1f}%\n"
        f"[bold]Actual Existing Customer Spend:[/bold] [{cap_color}]{cap.actual_existing_spend_pct:.1f}%[/{cap_color}] "
        f"({report.currency_code} {cap.actual_existing_customer_spend:,.2f})\n"
        f"[bold]Cap Status:[/bold] [{cap_color}]{'BREACHED' if cap.cap_exceeded else 'COMPLIANT'}[/{cap_color}]\n"
        f"- Finding: {cap.finding}"
    )
    console.print(Panel(cap_text, title="[bold]Check 3: Existing Customer Budget Cap Compliance[/bold]", border_style=cap_color))

    # 5. Strategic Directives
    dir_text = Text()
    for rec in report.recommendations:
        dir_text.append(f"- {rec}\n", style="cyan")
    console.print(Panel(dir_text, title="[bold]Actionable Directives & Remediation Roadmap[/bold]", border_style="blue"))
