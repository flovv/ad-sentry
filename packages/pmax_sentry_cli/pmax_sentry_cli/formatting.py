from __future__ import annotations

from decimal import Decimal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pmax_sentry_core.models import (
    AccountInfo,
    CampaignInfo,
    DeliveryReport,
    SearchInsightReport,
)

console = Console()


def render_dry_run_panel(
    account: AccountInfo,
    campaigns: list[CampaignInfo],
    start_date: str,
    end_date: str,
    export_format: str,
) -> None:
    text = Text()
    text.append(f"Customer ID:      {account.customer_id}\n", style="bold cyan")
    text.append(f"Account Name:     {account.descriptive_name}\n")
    text.append(f"Currency:         {account.currency_code}\n", style="bold yellow")
    text.append(f"Timezone:         {account.time_zone}\n")
    text.append(f"Date Window:      {start_date} to {end_date}\n", style="bold green")
    text.append(f"Eligible PMax:    {len(campaigns)} campaigns (")
    enabled = sum(1 for c in campaigns if c.status == "ENABLED")
    paused = sum(1 for c in campaigns if c.status == "PAUSED")
    text.append(f"{enabled} ENABLED, {paused} PAUSED)\n")
    text.append(f"Target Format:    {export_format.upper()}\n")

    console.print(
        Panel(
            text,
            title="[bold blue]PMax Sentry — Dry-Run Preview[/bold blue]",
            subtitle="[dim]Verify account boundaries before executing report[/dim]",
            border_style="blue",
        )
    )


def render_campaigns_table(account: AccountInfo, campaigns: list[CampaignInfo]) -> None:
    table = Table(
        title=f"Performance Max Campaigns — {account.descriptive_name} ({account.customer_id})",
        header_style="bold magenta",
    )
    table.add_column("Campaign ID", style="cyan")
    table.add_column("Campaign Name", style="bold white")
    table.add_column("Status", justify="center")
    table.add_column("Bidding Strategy")
    table.add_column("Target ROAS", justify="right")

    for camp in campaigns:
        status_style = "green" if camp.status == "ENABLED" else "yellow" if camp.status == "PAUSED" else "red"
        troas_str = f"{camp.target_roas:.2f}x" if camp.target_roas else "—"
        table.add_row(
            camp.id,
            camp.name,
            f"[{status_style}]{camp.status}[/{status_style}]",
            camp.bidding_strategy_type or "—",
            troas_str,
        )

    console.print(table)


def render_delivery_report(report: DeliveryReport) -> None:
    # 1. Summary Header
    summary_text = (
        f"[bold]Customer:[/bold] {report.customer_id} | "
        f"[bold]Window:[/bold] {report.start_date} to {report.end_date} | "
        f"[bold]Currency:[/bold] {report.currency_code} | "
        f"[bold]API Version:[/bold] {report.api_version}\n"
        f"[bold]Reported Total Cost:[/bold] {report.currency_code} {report.total_cost:,.2f} | "
        f"[bold]Attributed Value:[/bold] {report.currency_code} {report.total_conversion_value:,.2f} | "
        f"[bold]Reported ROAS:[/bold] {report.reported_roas:.2f}x"
        if report.reported_roas is not None
        else f"[bold]Reported ROAS:[/bold] N/A"
    )
    console.print(Panel(summary_text, title="[bold]Reported PMax Delivery Summary[/bold]", border_style="cyan"))

    # 2. Channel x Format Table
    table = Table(
        title="Reported Delivery Mix (Channel × Format Dimensions)",
        header_style="bold cyan",
    )
    table.add_column("Channel", style="bold white")
    table.add_column("Product Data?", justify="center")
    table.add_column("Video?", justify="center")
    table.add_column("Spend", justify="right", style="yellow")
    table.add_column("Share", justify="right")
    table.add_column("Impr.", justify="right")
    table.add_column("Clicks", justify="right")
    table.add_column("Conv.", justify="right")
    table.add_column("Conv. Value", justify="right")
    table.add_column("ROAS", justify="right", style="bold green")

    # Aggregate by channel x format
    agg: dict[tuple[str, bool | None, bool | None], dict[str, Any]] = {}
    total_cost = report.total_cost

    for r in report.rows:
        key = (r.channel, r.uses_product_data, r.uses_video)
        if key not in agg:
            agg[key] = {
                "cost": Decimal(0),
                "impressions": 0,
                "clicks": 0,
                "conversions": Decimal(0),
                "conversion_value": Decimal(0),
            }
        agg[key]["cost"] += r.cost
        agg[key]["impressions"] += r.impressions
        agg[key]["clicks"] += r.clicks
        agg[key]["conversions"] += r.conversions
        agg[key]["conversion_value"] += r.conversion_value

    sorted_keys = sorted(agg.keys(), key=lambda k: agg[k]["cost"], reverse=True)
    for channel, uses_prod, uses_vid in sorted_keys:
        d = agg[(channel, uses_prod, uses_vid)]
        share = (d["cost"] / total_cost * 100) if total_cost > 0 else Decimal(0)
        roas = (d["conversion_value"] / d["cost"]) if d["cost"] > 0 else None
        prod_str = "Yes" if uses_prod is True else "No" if uses_prod is False else "—"
        vid_str = "Yes" if uses_vid is True else "No" if uses_vid is False else "—"
        roas_str = f"{roas:.2f}x" if roas is not None else "—"

        table.add_row(
            channel,
            prod_str,
            vid_str,
            f"{report.currency_code} {d['cost']:,.2f}",
            f"{share:.1f}%",
            f"{d['impressions']:,}",
            f"{d['clicks']:,}",
            f"{d['conversions']:,.1f}",
            f"{report.currency_code} {d['conversion_value']:,.2f}",
            roas_str,
        )

    console.print(table)

    # 3. Reconciliation Panel
    cov = report.coverage
    status_color = "green" if cov.status == "COMPLETE" else "yellow" if cov.status == "PARTIAL" else "red"
    cov_text = Text()
    cov_text.append(f"Reconciliation Status:  [{status_color}]{cov.status}[/{status_color}]\n", style="bold")
    cov_text.append(
        f"Segmented Cost Sum:     {report.currency_code} {(Decimal(cov.segmented_cost_micros) / Decimal(1_000_000)):,.2f} "
        f"({cov.segmented_cost_micros:,} micros)\n"
    )
    cov_text.append(
        f"Campaign Total Cost:    {report.currency_code} {(Decimal(cov.unsegmented_cost_micros) / Decimal(1_000_000)):,.2f} "
        f"({cov.unsegmented_cost_micros:,} micros)\n"
    )
    cov_text.append(
        f"Raw Difference:         {report.currency_code} {(Decimal(cov.difference_micros) / Decimal(1_000_000)):,.2f} "
        f"({cov.difference_micros:,} micros)\n"
    )
    ratio_str = f"{cov.coverage_ratio:.2%}" if cov.coverage_ratio is not None else "N/A"
    cov_text.append(f"Coverage Ratio:         {ratio_str}\n")
    for r in cov.reasons:
        cov_text.append(f"• {r}\n", style="dim")

    console.print(Panel(cov_text, title="[bold]Reconciliation Audit[/bold]", border_style=status_color))

    # 4. Cross-Campaign Overlap (if Demand Gen included)
    if report.cross_campaign_overlap:
        ov = report.cross_campaign_overlap
        ov_table = Table(
            title="Cross-Campaign Overlap & Inventory Collision (PMax vs. Demand Gen)",
            header_style="bold magenta",
        )
        ov_table.add_column("Channel / Surface", style="bold white")
        ov_table.add_column("PMax Spend", justify="right", style="cyan")
        ov_table.add_column("PMax Share", justify="right")
        ov_table.add_column("Demand Gen Spend", justify="right", style="magenta")
        ov_table.add_column("Demand Gen Share", justify="right")
        ov_table.add_column("Collision Status", justify="center")

        for s in ov.surface_breakdown:
            status = "[bold red]COLLISION[/bold red]" if s["is_shared"] else "[dim]Isolated[/dim]"
            ov_table.add_row(
                s["channel"],
                f"{report.currency_code} {s['pmax_spend']:,.2f}",
                f"{s['pmax_share']:.1f}%",
                f"{report.currency_code} {s['demand_gen_spend']:,.2f}",
                f"{s['demand_gen_share']:.1f}%",
                status,
            )
        console.print(ov_table)

        sev_color = "red" if ov.overlap_severity == "HIGH" else "yellow" if ov.overlap_severity == "MEDIUM" else "green"
        ov_text = Text()
        ov_text.append(f"Overlap Severity:              [{sev_color}]{ov.overlap_severity}[/{sev_color}]\n", style="bold")
        ov_text.append(f"PMax View-Through Share:       {ov.pmax_view_through_ratio:.1%} of attributed conversions\n")
        ov_text.append(f"Demand Gen View-Through Share: {ov.demand_gen_view_through_ratio:.1%} of attributed conversions (EVC / passive views)\n\n", style="bold yellow" if ov.demand_gen_view_through_ratio > 0.3 else "")
        ov_text.append("Strategic Directives:\n", style="bold")
        for rec in ov.recommendations:
            ov_text.append(f"- {rec}\n", style="cyan")

        console.print(Panel(ov_text, title="[bold]Cross-Campaign Attribution & De-Duplication Audit[/bold]", border_style="magenta"))

    # 5. Mandatory Disclaimer (Spec 13)
    disclaimer = Text(
        "This report shows reported PMax delivery by channel and format. "
        "Incrementality analysis needs business outcome data and a suitable measurement design.",
        style="italic cyan",
    )
    console.print(Panel(disclaimer, border_style="dim"))


def render_search_insights_report(report: SearchInsightReport) -> None:
    table = Table(
        title=f"Search Demand Insights — Customer {report.customer_id}",
        header_style="bold magenta",
    )
    table.add_column("Category Label", style="bold white")
    table.add_column("Clicks", justify="right")
    table.add_column("Impressions", justify="right")
    table.add_column("Search Volume", justify="right")
    table.add_column("Conversions", justify="right")
    table.add_column("Conv. Value", justify="right")

    for r in report.rows:
        vol_str = f"{r.search_volume:,}" if r.search_volume is not None else "—"
        table.add_row(
            r.category_label,
            f"{r.clicks:,}",
            f"{r.impressions:,}",
            vol_str,
            f"{r.conversions:,.1f}",
            f"{r.conversion_value:,.2f}",
        )

    console.print(table)

    if report.brand_diagnostic:
        diag = report.brand_diagnostic
        diag_text = (
            f"[bold]Classifier Version:[/bold] {diag.classifier_version}\n"
            f"[bold]Brand Dictionary:[/bold] {', '.join(diag.brand_dictionary)}\n"
            f"[bold]Classifiable Query Share:[/bold] {diag.classifiable_query_share:.1%}\n"
            f"[bold]Brand Share:[/bold] {diag.brand_query_share:.1%} | "
            f"[bold]Generic Share:[/bold] {diag.generic_query_share:.1%} | "
            f"[bold]Unknown Share:[/bold] {diag.unknown_query_share:.1%}\n"
        )
        for n in diag.notes:
            diag_text += f"[dim]• {n}[/dim]\n"
        console.print(Panel(diag_text, title="[bold]Brand Diagnostic Summary[/bold]", border_style="blue"))

    notice = Text(
        "Search term insights are informational search-demand categories and do NOT include cost metrics. "
        "Do not infer brand-search spend or budget allocation from search-term insights.",
        style="bold yellow",
    )
    console.print(Panel(notice, border_style="yellow"))
