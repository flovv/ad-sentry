from __future__ import annotations

import datetime as dt
from decimal import Decimal
import html
import json
from pathlib import Path
from typing import Any, Optional

from pmax_sentry_core.models import DeliveryReport, SearchInsightReport
from services.decision_contracts.models import DecisionContract
from services.incrementality.models import EconomicHurdleResult


def generate_white_label_html_deck(
    delivery_report: DeliveryReport,
    hurdle: Optional[EconomicHurdleResult] = None,
    decision_contract: Optional[DecisionContract] = None,
    search_insights: Optional[SearchInsightReport] = None,
    agency_name: str = "Performance Media Agency",
    agency_logo_url: Optional[str] = None,
    client_brand_name: str = "Client Brand",
    primary_color_hex: str = "#2563eb",
) -> str:
    """
    Generates a standalone, client-ready interactive HTML audit deck with White-Label agency branding.
    Can be opened directly in any browser or saved as PDF for client meetings and pitches.
    """
    total_cost = delivery_report.total_cost
    total_val = delivery_report.total_conversion_value
    roas_str = f"{delivery_report.reported_roas:.2f}x" if delivery_report.reported_roas else "N/A"
    cov = delivery_report.coverage

    # Channel aggregation
    agg_channels: dict[str, Decimal] = {}
    for r in delivery_report.rows:
        agg_channels[r.channel] = agg_channels.get(r.channel, Decimal(0)) + r.cost
    sorted_channels = sorted(agg_channels.items(), key=lambda x: x[1], reverse=True)

    status_badge_color = "#10b981" if cov.status == "COMPLETE" else "#f59e0b" if cov.status == "PARTIAL" else "#ef4444"

    hurdle_card = ""
    if hurdle:
        hurdle_card = f"""
        <div class="kpi-card">
          <div class="kpi-label">Break-Even Hurdle (1/μ)</div>
          <div class="kpi-value" style="color: #6366f1;">{hurdle.breakeven_iroas:.2f}x</div>
          <div class="kpi-sub">Target Margin: {hurdle.contribution_margin_rate:.1%}</div>
        </div>
        """

    channel_rows_html = ""
    for ch, cost in sorted_channels:
        share = (cost / total_cost * 100) if total_cost > 0 else Decimal(0)
        channel_rows_html += f"""
        <tr>
          <td style="font-weight: 600;">{html.escape(ch)}</td>
          <td style="text-align: right;">{delivery_report.currency_code} {cost:,.2f}</td>
          <td style="text-align: right;">{share:.1f}%</td>
          <td>
            <div style="background: #e5e7eb; border-radius: 4px; overflow: hidden; height: 10px; width: 100%;">
              <div style="background: {primary_color_hex}; height: 100%; width: {share:.1f}%;"></div>
            </div>
          </td>
        </tr>
        """

    reasons_html = "".join(f"<li>{html.escape(r)}</li>" for r in cov.reasons)

    search_insights_section = ""
    if search_insights and search_insights.rows:
        rows_si = ""
        for sr in search_insights.rows[:10]:
            vol = f"{sr.search_volume:,}" if sr.search_volume is not None else "—"
            rows_si += f"""
            <tr>
              <td>{html.escape(sr.category_label)}</td>
              <td style="text-align: right;">{sr.clicks:,}</td>
              <td style="text-align: right;">{sr.impressions:,}</td>
              <td style="text-align: right;">{vol}</td>
              <td style="text-align: right;">{sr.conversions:.1f}</td>
            </tr>
            """
        search_insights_section = f"""
        <div class="card">
          <h2>Search Demand Insight Categories</h2>
          <p class="notice">⚠️ Search categories reflect consumer search demand volume only; they do NOT contain ad cost or spend metrics.</p>
          <table>
            <thead>
              <tr>
                <th>Category Label</th>
                <th style="text-align: right;">Clicks</th>
                <th style="text-align: right;">Impressions</th>
                <th style="text-align: right;">Search Volume</th>
                <th style="text-align: right;">Conversions</th>
              </tr>
            </thead>
            <tbody>
              {rows_si}
            </tbody>
          </table>
        </div>
        """

    contract_section = ""
    if decision_contract:
        assumptions_html = "".join(f"<li>{html.escape(a)}</li>" for a in decision_contract.assumptions_and_limitations)
        contract_section = f"""
        <div class="card">
          <h2>Decision Contract & Recommendations</h2>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div>
              <strong>Contract ID:</strong> <code>{html.escape(decision_contract.contract_id)}</code><br>
              <strong>Evidence Class:</strong> <span class="badge" style="background: #1e3a8a; color: #93c5fd;">{decision_contract.evidence_class}</span><br>
              <strong>Recommendation:</strong> <span class="badge" style="background: #065f46; color: #a7f3d0;">{decision_contract.recommendation_type}</span>
            </div>
            <div>
              <strong>Valid Until:</strong> {decision_contract.valid_until}<br>
              <strong>Human Approval Required:</strong> Yes (Read-Only Guarantee)
            </div>
          </div>
          <h3>Assumptions & Limitations</h3>
          <ul>
            {assumptions_html}
          </ul>
        </div>
        """

    logo_markup = f'<img src="{html.escape(agency_logo_url)}" alt="Logo" style="height: 40px; margin-right: 15px;">' if agency_logo_url else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PMax Delivery & Incrementality Audit — {html.escape(client_brand_name)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{ --primary: {primary_color_hex}; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 2rem; }}
    .container {{ max-width: 1080px; margin: 0 auto; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
    .brand-title {{ font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 0; }}
    .agency-subtitle {{ font-size: 0.9rem; color: #64748b; margin-top: 0.25rem; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .kpi-card {{ background: #fff; padding: 1.25rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .kpi-label {{ font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 0.5rem; }}
    .kpi-value {{ font-size: 1.75rem; font-weight: 800; color: #0f172a; }}
    .kpi-sub {{ font-size: 0.8rem; color: #64748b; margin-top: 0.25rem; }}
    .card {{ background: #fff; padding: 1.5rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 2rem; }}
    h2 {{ font-size: 1.25rem; margin-top: 0; color: #0f172a; border-bottom: 1px solid #f1f5f9; padding-bottom: 0.75rem; }}
    h3 {{ font-size: 1rem; color: #334155; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-top: 1rem; }}
    th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #f1f5f9; }}
    th {{ background: #f8fafc; font-weight: 600; color: #475569; }}
    .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
    .notice {{ background: #fef3c7; color: #92400e; padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.85rem; border-left: 4px solid #f59e0b; margin: 1rem 0; }}
    .footer {{ text-align: center; font-size: 0.8rem; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 1.5rem; margin-top: 3rem; }}
    @media print {{ body {{ background: #fff; padding: 0; }} .card {{ box-shadow: none; border: 1px solid #cbd5e1; }} }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div style="display: flex; align-items: center;">
        {logo_markup}
        <div>
          <h1 class="brand-title">{html.escape(client_brand_name)} — Performance Max Audit Deck</h1>
          <div class="agency-subtitle">Prepared by {html.escape(agency_name)} | Window: {delivery_report.start_date} to {delivery_report.end_date}</div>
        </div>
      </div>
      <div>
        <span class="badge" style="background: #e2e8f0; color: #334155;">API {html.escape(delivery_report.api_version)}</span>
        <span class="badge" style="background: {status_badge_color}; color: #fff;">{cov.status}</span>
      </div>
    </div>

    <!-- Executive KPIs -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Audited Spend</div>
        <div class="kpi-value">{delivery_report.currency_code} {total_cost:,.2f}</div>
        <div class="kpi-sub">{delivery_report.total_impressions:,} imps | {delivery_report.total_clicks:,} clicks</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Attributed Value</div>
        <div class="kpi-value">{delivery_report.currency_code} {total_val:,.2f}</div>
        <div class="kpi-sub">{delivery_report.total_conversions:,.1f} reported conversions</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Platform ROAS</div>
        <div class="kpi-value" style="color: {primary_color_hex};">{roas_str}</div>
        <div class="kpi-sub">Attributed Value / Ad Spend</div>
      </div>
      {hurdle_card}
    </div>

    <!-- Delivery Mix Table -->
    <div class="card">
      <h2>Reported Delivery Mix Across Channels</h2>
      <p style="font-size: 0.9rem; color: #64748b;">
        Delivery distribution segmented via supported Google Ads API channels. Format dimensions (product data & video) are evaluated orthogonally.
      </p>
      <table>
        <thead>
          <tr>
            <th>Channel</th>
            <th style="text-align: right;">Spend</th>
            <th style="text-align: right;">Share</th>
            <th style="width: 30%;">Visual Distribution</th>
          </tr>
        </thead>
        <tbody>
          {channel_rows_html}
        </tbody>
      </table>
    </div>

    <!-- Reconciliation Audit -->
    <div class="card">
      <h2>Account Reconciliation & Coverage Audit</h2>
      <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
        <div><strong>Reconciliation Status:</strong> <span class="badge" style="background: {status_badge_color}; color: #fff;">{cov.status}</span></div>
        <div><strong>Coverage Ratio:</strong> {cov.coverage_ratio if cov.coverage_ratio is not None else 'N/A'}</div>
        <div><strong>Raw Difference:</strong> {delivery_report.currency_code} {(Decimal(cov.difference_micros)/Decimal(1000000)):,.2f}</div>
      </div>
      <ul>
        {reasons_html}
      </ul>
      <p class="notice">
        <strong>Measurement Discipline:</strong> Discrepancies between campaign totals and segmented reporting are preserved as unclassified differences. They are never hidden with artificial formulas and never assumed to belong to Display, Video, or waste.
      </p>
    </div>

    {search_insights_section}
    {contract_section}

    <div class="footer">
      Generated with PMax Sentry Pro for {html.escape(agency_name)}. Verified read-only execution. No live campaign mutations.
    </div>
  </div>
</body>
</html>
"""
