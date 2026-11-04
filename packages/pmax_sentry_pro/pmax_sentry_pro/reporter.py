from __future__ import annotations

import datetime as dt
from decimal import Decimal
import html
import json
from pathlib import Path
from typing import Any, Optional

from pmax_sentry_core.meta_models import MetaAscAuditReport
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

    status_badge_style = (
        "background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;"
        if cov.status == "COMPLETE"
        else "background: #fffbeb; color: #92400e; border: 1px solid #fde68a;"
        if cov.status == "PARTIAL"
        else "background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;"
    )

    hurdle_card = ""
    if hurdle:
        hurdle_card = f"""
        <div class="kpi-card">
          <div class="kpi-label">Break-Even Hurdle (1/μ)</div>
          <div class="kpi-value" style="color: #4f46e5;">{hurdle.breakeven_iroas:.2f}x</div>
          <div class="kpi-sub">Target Margin: {hurdle.contribution_margin_rate:.1%}</div>
        </div>
        """

    channel_rows_html = ""
    for ch, cost in sorted_channels:
        share = (cost / total_cost * 100) if total_cost > 0 else Decimal(0)
        channel_rows_html += f"""
        <tr>
          <td style="font-weight: 600;">{html.escape(ch)}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{delivery_report.currency_code} {cost:,.2f}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{share:.1f}%</td>
          <td>
            <div style="background: #e2e8f0; border-radius: 4px; overflow: hidden; height: 8px; width: 100%;">
              <div style="background: {primary_color_hex}; height: 100%; width: {share:.1f}%; border-radius: 4px;"></div>
            </div>
          </td>
        </tr>
        """

    reasons_html = "".join(f"<li>{html.escape(r)}</li>" for r in cov.reasons)

    # Asset Group Quality Grader Section
    asset_group_section = ""
    if delivery_report.asset_group_audit and delivery_report.asset_group_audit.asset_groups:
        aga = delivery_report.asset_group_audit
        grade_badge_style = (
            "background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;"
            if aga.overall_grade in ("A+", "A")
            else "background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe;"
            if aga.overall_grade == "B"
            else "background: #fffbeb; color: #92400e; border: 1px solid #fde68a;"
            if aga.overall_grade == "C"
            else "background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;"
        )

        ag_rows_html = ""
        for ag in aga.asset_groups:
            str_style = (
                "color: #065f46;" if ag.ad_strength == "EXCELLENT"
                else "color: #1e40af;" if ag.ad_strength == "GOOD"
                else "color: #92400e;" if ag.ad_strength == "AVERAGE"
                else "color: #991b1b;"
            )
            v_badge = (
                '<span class="badge" style="background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;">Yes</span>'
                if ag.has_vertical_video
                else '<span class="badge" style="background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;">MISSING (Junk Video Risk)</span>'
            )
            aud_badge = (
                '<span class="badge" style="background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;">Yes</span>'
                if ag.has_audience_signals
                else '<span class="badge" style="background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;">NO SEED</span>'
            )
            issues_text = "; ".join(ag.critical_issues) if ag.critical_issues else "Flawless asset coverage"

            ag_rows_html += f"""
            <tr>
              <td>
                <strong>{html.escape(ag.asset_group_name)}</strong><br>
                <span style="font-size: 0.75rem; color: #64748b;">{html.escape(ag.campaign_name)}</span>
              </td>
              <td style="text-align: center; font-weight: 600; {str_style}">{html.escape(ag.ad_strength)}</td>
              <td style="text-align: center; font-variant-numeric: tabular-nums;">{ag.headlines_count}/15</td>
              <td style="text-align: center; font-variant-numeric: tabular-nums;">{ag.images_count}</td>
              <td style="text-align: center;">{v_badge}</td>
              <td style="text-align: center;">{aud_badge}</td>
              <td style="text-align: right; font-weight: 700; font-variant-numeric: tabular-nums;">{ag.score}/100</td>
              <td style="text-align: center;"><span class="badge" style="{grade_badge_style}">{html.escape(ag.grade)}</span></td>
            </tr>
            <tr>
              <td colspan="8" style="background: #f8fafc; font-size: 0.8125rem; color: #475569; padding: 0.4rem 0.75rem;">
                <strong>Issues & Action:</strong> {html.escape(issues_text)}
              </td>
            </tr>
            """

        ag_recs_html = "".join(f"<li>{html.escape(r)}</li>" for r in aga.recommendations)

        asset_group_section = f"""
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h2>Asset Group Creative Completeness & Quality Grader</h2>
            <div>
              <span style="font-size: 0.875rem; color: #64748b; margin-right: 0.5rem;">Overall Grade:</span>
              <span class="badge" style="{grade_badge_style} font-size: 0.95rem; padding: 0.35rem 0.75rem;">{aga.overall_grade} ({aga.average_score:.1f}/100)</span>
            </div>
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.25rem;">
            <div class="kpi-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
              <div class="kpi-label">Asset Groups Audited</div>
              <div class="kpi-value" style="font-size: 1.4rem;">{aga.total_asset_groups}</div>
              <div class="kpi-sub">PMax Creative Containers</div>
            </div>
            <div class="kpi-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
              <div class="kpi-label">Missing 9:16 Shorts Video</div>
              <div class="kpi-value" style="font-size: 1.4rem; color: #b91c1c;">{aga.missing_vertical_video_count}</div>
              <div class="kpi-sub">Triggers auto-generated junk video</div>
            </div>
            <div class="kpi-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
              <div class="kpi-label">Missing Audience Signals</div>
              <div class="kpi-value" style="font-size: 1.4rem; color: #d97706;">{aga.missing_audience_signals_count}</div>
              <div class="kpi-sub">Algorithm bidding unguided</div>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Asset Group</th>
                <th style="text-align: center;">Ad Strength</th>
                <th style="text-align: center;">Headlines</th>
                <th style="text-align: center;">Images</th>
                <th style="text-align: center;">9:16 Video</th>
                <th style="text-align: center;">Audience Seed</th>
                <th style="text-align: right;">Score</th>
                <th style="text-align: center;">Grade</th>
              </tr>
            </thead>
            <tbody>
              {ag_rows_html}
            </tbody>
          </table>
          <div class="notice">
            <strong>Agency Insight:</strong> Performance Max requires dedicated 9:16 vertical videos. When missing, Google's algorithm auto-stitches existing images into blurry, low-resolution slideshow videos that inflate bounce rates on YouTube Shorts.
          </div>
          <h3 style="margin-top: 1rem;">Creative Optimization Directives:</h3>
          <ul>
            {ag_recs_html}
          </ul>
        </div>
        """

    # Product Feed Zombie Products Section
    product_feed_section = ""
    if delivery_report.product_feed_audit and delivery_report.product_feed_audit.total_products_audited > 0:
        pfa = delivery_report.product_feed_audit
        zombie_badge_style = (
            "background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;"
            if pfa.zombie_spend_share > 15
            else "background: #fffbeb; color: #92400e; border: 1px solid #fde68a;"
        )

        zombie_rows_html = ""
        for z in pfa.top_zombie_products:
            zombie_rows_html += f"""
            <tr>
              <td style="font-family: monospace; font-size: 0.8125rem;">{html.escape(z.product_id)}</td>
              <td><strong>{html.escape(z.title)}</strong><br><span style="color: #64748b; font-size: 0.75rem;">Brand: {html.escape(z.brand or 'Generic')}</span></td>
              <td style="text-align: right; font-weight: 700; color: #b91c1c; font-variant-numeric: tabular-nums;">{delivery_report.currency_code} {z.cost:,.2f}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{z.clicks:,}</td>
              <td style="text-align: center; color: #b91c1c; font-weight: 700;">0.0</td>
              <td style="font-size: 0.8125rem; color: #334155;">{html.escape(z.suggested_action)}</td>
            </tr>
            """

        feed_actions_html = "".join(f"<li>{html.escape(a)}</li>" for a in pfa.action_plan)

        product_feed_section = f"""
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h2>Shopping Feed & "Zombie Products" Waste Audit</h2>
            <span class="badge" style="{zombie_badge_style} font-size: 0.9rem; padding: 0.35rem 0.75rem;">
              {pfa.zombie_spend_share:.1f}% Budget Bleed
            </span>
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.25rem;">
            <div class="kpi-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
              <div class="kpi-label">Audited Feed SKUs</div>
              <div class="kpi-value" style="font-size: 1.4rem;">{pfa.total_products_audited:,}</div>
              <div class="kpi-sub">Merchant Center Feed</div>
            </div>
            <div class="kpi-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
              <div class="kpi-label">Zombie SKUs (0 Conv.)</div>
              <div class="kpi-value" style="font-size: 1.4rem; color: #b91c1c;">{pfa.zombie_products_count}</div>
              <div class="kpi-sub">{pfa.zombie_products_count / pfa.total_products_audited:.1%} of active catalog</div>
            </div>
            <div class="kpi-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
              <div class="kpi-label">Wasted Zombie Spend</div>
              <div class="kpi-value" style="font-size: 1.4rem; color: #b91c1c;">{delivery_report.currency_code} {pfa.zombie_spend:,.2f}</div>
              <div class="kpi-sub">{pfa.zombie_spend_share:.1f}% of entire feed spend</div>
            </div>
            <div class="kpi-card" style="box-shadow: none; border: 1px solid #e2e8f0;">
              <div class="kpi-label">Reclaimable Savings</div>
              <div class="kpi-value" style="font-size: 1.4rem; color: #065f46;">{delivery_report.currency_code} {pfa.estimated_monthly_savings:,.2f}/mo</div>
              <div class="kpi-sub">Immediate reallocation upside</div>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>SKU ID</th>
                <th>Product Title</th>
                <th style="text-align: right;">Wasted Spend</th>
                <th style="text-align: right;">Clicks</th>
                <th style="text-align: center;">Conversions</th>
                <th>Agency Action Directive</th>
              </tr>
            </thead>
            <tbody>
              {zombie_rows_html}
            </tbody>
          </table>
          <div class="notice">
            <strong>Zombie SKU Mechanics:</strong> In standard PMax setups, non-converting products slowly siphon off 15–25% of total ad spend without meeting Target ROAS hurdles. Setting <code>Custom Label 0 = 'zombie'</code> or negative listing filters halts this waste immediately.
          </div>
          <h3 style="margin-top: 1rem;">Immediate Action Plan:</h3>
          <ul>
            {feed_actions_html}
          </ul>
        </div>
        """


    search_insights_section = ""
    if search_insights and search_insights.rows:
        rows_si = ""
        for sr in search_insights.rows[:10]:
            vol = f"{sr.search_volume:,}" if sr.search_volume is not None else "—"
            rows_si += f"""
            <tr>
              <td>{html.escape(sr.category_label)}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{sr.clicks:,}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{sr.impressions:,}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{vol}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{sr.conversions:.1f}</td>
            </tr>
            """
        search_insights_section = f"""
        <div class="card">
          <h2>Search Demand Insight Categories</h2>
          <p class="notice"><strong>Demand Notice:</strong> Search categories reflect consumer search demand volume only; they do not contain ad cost or spend metrics.</p>
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

    overlap_section = ""
    if delivery_report.cross_campaign_overlap:
        ov = delivery_report.cross_campaign_overlap
        ov_rows = ""
        for s in ov.surface_breakdown:
            status_badge = (
                '<span class="badge" style="background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;">Collision</span>'
                if s["is_shared"]
                else '<span class="badge" style="background: #f8fafc; color: #475569; border: 1px solid #e2e8f0;">Isolated</span>'
            )
            ov_rows += f"""
            <tr>
              <td style="font-weight: 600;">{html.escape(s["channel"])}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{delivery_report.currency_code} {s["pmax_spend"]:,.2f}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{s["pmax_share"]:.1f}%</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{delivery_report.currency_code} {s["demand_gen_spend"]:,.2f}</td>
              <td style="text-align: right; font-variant-numeric: tabular-nums;">{s["demand_gen_share"]:.1f}%</td>
              <td style="text-align: center;">{status_badge}</td>
            </tr>
            """
        recs_list = "".join(f"<li>{html.escape(r)}</li>" for r in ov.recommendations)
        sev_badge = (
            '<span class="badge" style="background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;">HIGH</span>'
            if ov.overlap_severity == "HIGH"
            else '<span class="badge" style="background: #fffbeb; color: #92400e; border: 1px solid #fde68a;">MEDIUM</span>'
            if ov.overlap_severity == "MEDIUM"
            else '<span class="badge" style="background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;">LOW</span>'
        )
        overlap_section = f"""
        <div class="card">
          <h2>Cross-Campaign Overlap & Inventory Collision (PMax vs. Demand Gen)</h2>
          <div style="display: flex; gap: 2rem; margin-bottom: 1.25rem; flex-wrap: wrap;">
            <div><strong>Inventory Overlap Severity:</strong> {sev_badge}</div>
            <div><strong>PMax View-Through Share:</strong> {float(ov.pmax_view_through_ratio * 100):.1f}%</div>
            <div><strong>Demand Gen View-Through Share:</strong> <strong style="color: #b91c1c;">{float(ov.demand_gen_view_through_ratio * 100):.1f}% (EVC)</strong></div>
          </div>
          <table>
            <thead>
              <tr>
                <th>Surface / Placement</th>
                <th style="text-align: right;">PMax Spend</th>
                <th style="text-align: right;">PMax Share</th>
                <th style="text-align: right;">Demand Gen Spend</th>
                <th style="text-align: right;">Demand Gen Share</th>
                <th style="text-align: center;">Collision Status</th>
              </tr>
            </thead>
            <tbody>
              {ov_rows}
            </tbody>
          </table>
          <div class="notice">
            <strong>Cross-Campaign Attribution Warning:</strong> High View-Through (Engaged-View) shares in Demand Gen indicate potential conversion inflation and double-attribution with subsequent PMax Search/Shopping touchpoints.
          </div>
          <h3 style="margin-top: 1rem;">Action Directives for Entanglement:</h3>
          <ul>
            {recs_list}
          </ul>
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
              <strong>Evidence Class:</strong> <span class="badge" style="background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe;">{decision_contract.evidence_class}</span><br>
              <strong>Recommendation:</strong> <span class="badge" style="background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;">{decision_contract.recommendation_type}</span>
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
    * {{ box-sizing: border-box; }}
    ::selection {{ background: #dbeafe; color: #1e3a8a; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      margin: 0;
      padding: 2.5rem 1.5rem;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }}
    .container {{ max-width: 1040px; margin: 0 auto; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .brand-title {{
      font-size: 1.5rem;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: -0.02em;
      margin: 0;
    }}
    .agency-subtitle {{
      font-size: 0.875rem;
      color: #475569;
      margin-top: 0.35rem;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .kpi-card {{
      background: #ffffff;
      padding: 1.25rem 1.5rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
    }}
    .kpi-label {{
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #475569;
      margin-bottom: 0.5rem;
    }}
    .kpi-value {{
      font-size: 1.875rem;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
    }}
    .kpi-sub {{
      font-size: 0.8125rem;
      color: #475569;
      margin-top: 0.35rem;
      font-variant-numeric: tabular-nums;
    }}
    .card {{
      background: #ffffff;
      padding: 1.75rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
      margin-bottom: 2rem;
    }}
    h2 {{
      font-size: 1.25rem;
      font-weight: 600;
      color: #0f172a;
      letter-spacing: -0.015em;
      margin-top: 0;
      margin-bottom: 1rem;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 0.75rem;
    }}
    h3 {{
      font-size: 0.9375rem;
      font-weight: 600;
      color: #1e293b;
      margin-top: 1.25rem;
      margin-bottom: 0.5rem;
    }}
    p {{ color: #334155; font-size: 0.9375rem; }}
    ul {{ margin-top: 0.5rem; padding-left: 1.25rem; color: #334155; font-size: 0.9375rem; }}
    li {{ margin-bottom: 0.35rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
      margin-top: 1.25rem;
      font-variant-numeric: tabular-nums;
    }}
    th, td {{
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid #f1f5f9;
    }}
    th {{
      background: #f8fafc;
      font-weight: 600;
      color: #334155;
      font-size: 0.8125rem;
      letter-spacing: 0.02em;
    }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .notice {{
      background: #fffbeb;
      color: #78350f;
      border: 1px solid #fde68a;
      padding: 0.85rem 1.15rem;
      border-radius: 6px;
      font-size: 0.875rem;
      margin: 1.25rem 0;
      line-height: 1.45;
    }}
    .footer {{
      text-align: center;
      font-size: 0.8125rem;
      color: #475569;
      border-top: 1px solid #e2e8f0;
      padding-top: 1.75rem;
      margin-top: 3rem;
    }}
    @media print {{
      body {{ background: #ffffff; padding: 0; }}
      .card, .kpi-card {{ box-shadow: none; border: 1px solid #cbd5e1; }}
    }}
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
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <span class="badge" style="background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe;">API {html.escape(delivery_report.api_version)}</span>
        <span class="badge" style="{status_badge_style}">{cov.status}</span>
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
      <p style="font-size: 0.9375rem; color: #475569; margin-bottom: 0;">
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
      <div style="display: flex; gap: 2rem; margin-bottom: 1rem; flex-wrap: wrap;">
        <div><strong>Reconciliation Status:</strong> <span class="badge" style="{status_badge_style}">{cov.status}</span></div>
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

    {asset_group_section}
    {product_feed_section}
    {search_insights_section}
    {overlap_section}
    {contract_section}

    <div class="footer">
      Generated with PMax Sentry Pro for {html.escape(agency_name)}. Verified read-only execution. No live campaign mutations.
    </div>
  </div>
</body>
</html>
"""


def generate_meta_asc_html_deck(
    audit_report: MetaAscAuditReport,
    agency_name: str = "Performance Media Agency",
    agency_logo_url: Optional[str] = None,
    client_brand_name: str = "Client Brand",
    primary_color_hex: str = "#0284c7",
) -> str:
    """
    Generates a standalone, client-ready interactive HTML audit deck for Meta Advantage+ Shopping Campaigns (ASC).
    Highlights Audience Network leakage, 1-Day View-Through inflation, and Existing Customer Cap compliance.
    """
    total_spend = audit_report.total_spend
    total_val = audit_report.total_conversion_value
    blended_roas = f"{audit_report.blended_roas:.2f}x"
    click_roas = f"{audit_report.click_only_roas:.2f}x"
    split = audit_report.attribution_split
    cap = audit_report.audience_cap_audit

    # Placement rows
    placement_rows_html = ""
    for p in audit_report.placement_rows:
        share = (p.spend / total_spend * 100) if total_spend > 0 else Decimal(0)
        roas_str = f"{p.roas:.2f}x" if p.roas else "—"
        badge_style = (
            "background: #fef2f2; color: #991b1b; border: 1px solid #fecaca;"
            if p.publisher_platform == "audience_network" and p.spend > 0
            else "background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe;"
        )
        platform_label = f"{p.publisher_platform.replace('_', ' ').title()} ({p.platform_position.replace('_', ' ').title()})"
        placement_rows_html += f"""
        <tr>
          <td style="font-weight: 600;">{html.escape(platform_label)}</td>
          <td style="text-align: center;"><span class="badge" style="{badge_style}">{html.escape(p.publisher_platform)}</span></td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{audit_report.currency_code} {p.spend:,.2f}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{share:.1f}%</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{p.clicks:,}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{roas_str}</td>
          <td>
            <div style="background: #e2e8f0; border-radius: 4px; overflow: hidden; height: 8px; width: 100%;">
              <div style="background: {primary_color_hex}; height: 100%; width: {share:.1f}%; border-radius: 4px;"></div>
            </div>
          </td>
        </tr>
        """

    # Creative formats
    format_rows_html = ""
    for f in audit_report.creative_formats:
        format_rows_html += f"""
        <tr>
          <td style="font-weight: 600;">{html.escape(f.format_type.replace('_', ' '))}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{audit_report.currency_code} {f.spend:,.2f}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{f.share:.1f}%</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{f.clicks:,}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{f.conversions:.1f}</td>
          <td style="text-align: right; font-variant-numeric: tabular-nums;">{f.roas:.2f}x</td>
        </tr>
        """

    recs_list = "".join(f"<li>{html.escape(r)}</li>" for r in audit_report.recommendations)

    hurdle_card = ""
    if audit_report.hurdle:
        hurdle_card = f"""
        <div class="kpi-card">
          <div class="kpi-label">Break-Even Hurdle (1/μ)</div>
          <div class="kpi-value" style="color: #4f46e5;">{audit_report.hurdle.breakeven_iroas:.2f}x</div>
          <div class="kpi-sub">Target Margin: {audit_report.hurdle.contribution_margin_rate:.1%}</div>
        </div>
        """

    logo_markup = f'<img src="{html.escape(agency_logo_url)}" alt="Logo" style="height: 40px; margin-right: 15px;">' if agency_logo_url else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Meta Advantage+ (ASC) Audit — {html.escape(client_brand_name)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{ --primary: {primary_color_hex}; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    ::selection {{ background: #e0f2fe; color: #0369a1; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      padding: 3rem 1.5rem;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }}
    .container {{ max-width: 1040px; margin: 0 auto; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 1.75rem;
      margin-bottom: 2.25rem;
      gap: 1.5rem;
      flex-wrap: wrap;
    }}
    .brand-title {{
      font-size: 1.625rem;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: -0.025em;
    }}
    .agency-subtitle {{
      font-size: 0.875rem;
      color: #475569;
      margin-top: 0.35rem;
    }}
    .badge {{
      display: inline-block;
      padding: 0.25rem 0.65rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .kpi-card {{
      background: #ffffff;
      padding: 1.35rem 1.5rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
    }}
    .kpi-label {{
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #475569;
      margin-bottom: 0.5rem;
    }}
    .kpi-value {{
      font-size: 1.875rem;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: -0.025em;
      font-variant-numeric: tabular-nums;
      line-height: 1.2;
    }}
    .kpi-sub {{
      font-size: 0.8125rem;
      color: #475569;
      margin-top: 0.4rem;
      font-variant-numeric: tabular-nums;
    }}
    .card {{
      background: #ffffff;
      padding: 1.75rem 2rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
      margin-bottom: 2rem;
    }}
    h2 {{
      font-size: 1.25rem;
      font-weight: 600;
      color: #0f172a;
      letter-spacing: -0.015em;
      margin-bottom: 0.5rem;
    }}
    .section-desc {{
      font-size: 0.875rem;
      color: #475569;
      margin-bottom: 1.25rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
      margin-top: 0.5rem;
      font-variant-numeric: tabular-nums;
    }}
    th, td {{
      padding: 0.8rem 1rem;
      text-align: left;
      border-bottom: 1px solid #f1f5f9;
    }}
    th {{
      background: #f8fafc;
      font-weight: 600;
      color: #475569;
      font-size: 0.75rem;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }}
    .notice {{
      background: #fffbeb;
      color: #78350f;
      border: 1px solid #fde68a;
      padding: 0.85rem 1.15rem;
      border-radius: 6px;
      font-size: 0.875rem;
      margin: 1.25rem 0;
      line-height: 1.5;
    }}
    .notice-critical {{
      background: #fef2f2;
      color: #991b1b;
      border: 1px solid #fecaca;
      padding: 1rem 1.25rem;
      border-radius: 6px;
      font-size: 0.875rem;
      margin: 1.25rem 0;
      line-height: 1.5;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
      margin-bottom: 1.25rem;
    }}
    ul.bullet-list {{
      padding-left: 1.25rem;
      color: #334155;
      font-size: 0.875rem;
      line-height: 1.6;
      margin-top: 0.5rem;
    }}
    ul.bullet-list li {{ margin-bottom: 0.35rem; }}
    .footer {{
      text-align: center;
      font-size: 0.8125rem;
      color: #475569;
      border-top: 1px solid #e2e8f0;
      padding-top: 2rem;
      margin-top: 3rem;
    }}
    @media print {{
      body {{ background: #ffffff; padding: 0; }}
      .card, .kpi-card {{ box-shadow: none; border: 1px solid #cbd5e1; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <div style="display: flex; align-items: center;">
        {logo_markup}
        <div>
          <h1 class="brand-title">{html.escape(client_brand_name)} — Meta Advantage+ Shopping Audit</h1>
          <div class="agency-subtitle">Prepared by {html.escape(agency_name)} &middot; Account: {audit_report.account_id} &middot; Window: {audit_report.start_date} to {audit_report.end_date}</div>
        </div>
      </div>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <span class="badge" style="background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe;">Meta Graph API</span>
        <span class="badge" style="background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;">AUDIT: COMPLETE</span>
      </div>
    </header>

    <!-- Executive KPIs -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Audited ASC Media Spend</div>
        <div class="kpi-value">{audit_report.currency_code} {total_spend:,.2f}</div>
        <div class="kpi-sub">Advantage+ Automated Budget</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Reported Conversion Value</div>
        <div class="kpi-value">{audit_report.currency_code} {total_val:,.2f}</div>
        <div class="kpi-sub">7d-Click + 1d-View Blended</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Blended Platform ROAS</div>
        <div class="kpi-value" style="color: {primary_color_hex};">{blended_roas}</div>
        <div class="kpi-sub">Includes passive view conversions</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Click-Only ROAS</div>
        <div class="kpi-value" style="color: #b91c1c;">{click_roas}</div>
        <div class="kpi-sub">Excludes 1-day view-through claims</div>
      </div>
      {hurdle_card}
    </div>

    <!-- Ghost ROAS Notice -->
    <div class="notice-critical">
      <strong>Ghost ROAS Alert:</strong> 1-Day View-Through attribution inflates reported Meta ROAS by <strong>+{float(split.ghost_roas_inflation_pct):.1f}%</strong>. Out of {split.total_reported_conversions:,.1f} total conversions, <strong>{float(split.view_through_dependency_ratio * 100):.1f}%</strong> were passive views without an ad click. Real click-driven efficiency is {click_roas}.
    </div>

    <!-- Placement Table -->
    <section class="card">
      <h2>Placement & Surface Distribution (Audience Network Leakage)</h2>
      <p class="section-desc">
        Meta ASC placement breakdown. Flags low-intent Audience Network delivery where casual gaming ads bleed media budget.
      </p>
      <table>
        <thead>
          <tr>
            <th>Placement</th>
            <th style="text-align: center;">Platform</th>
            <th style="text-align: right;">Spend</th>
            <th style="text-align: right;">Share</th>
            <th style="text-align: right;">Clicks</th>
            <th style="text-align: right;">ROAS</th>
            <th style="width: 25%;">Distribution</th>
          </tr>
        </thead>
        <tbody>
          {placement_rows_html}
        </tbody>
      </table>
      <div class="notice">
        <strong>Placement Notice:</strong> Audience Network accounts for <strong>{float(audit_report.audience_network_spend_share * 100):.1f}%</strong> of total spend. High click volumes paired with depressed ROAS indicate non-incremental accidental clicks.
      </div>
    </section>

    <!-- Existing Customer Cap -->
    <section class="card">
      <h2>Existing Customer Budget Cap Compliance</h2>
      <div class="grid-2">
        <div>
          <div style="font-size: 0.8125rem; font-weight: 600; color: #475569; text-transform: uppercase;">Configured Budget Cap</div>
          <div style="font-size: 1.25rem; font-weight: 700; color: #0f172a; margin-top: 0.25rem;">{cap.configured_cap_pct:.1f}% Target</div>
        </div>
        <div>
          <div style="font-size: 0.8125rem; font-weight: 600; color: #475569; text-transform: uppercase;">Actual Existing Customer Spend</div>
          <div style="font-size: 1.25rem; font-weight: 700; color: #b91c1c; margin-top: 0.25rem;">{cap.actual_existing_spend_pct:.1f}% ({audit_report.currency_code} {cap.actual_existing_customer_spend:,.2f})</div>
        </div>
      </div>
      <p style="font-size: 0.875rem; color: #334155; line-height: 1.5;">{html.escape(cap.finding)}</p>
    </section>

    <!-- Creative Formats -->
    <section class="card">
      <h2>Creative Format Balance (DPA vs. Video)</h2>
      <p class="section-desc">Spend allocation across Dynamic Product Ads (Catalog), Reels videos, and static images.</p>
      <table>
        <thead>
          <tr>
            <th>Format Type</th>
            <th style="text-align: right;">Spend</th>
            <th style="text-align: right;">Share</th>
            <th style="text-align: right;">Clicks</th>
            <th style="text-align: right;">Conversions</th>
            <th style="text-align: right;">ROAS</th>
          </tr>
        </thead>
        <tbody>
          {format_rows_html}
        </tbody>
      </table>
    </section>

    <!-- Strategic Directives -->
    <section class="card">
      <h2>Strategic Directives & Action Plan</h2>
      <ul class="bullet-list">
        {recs_list}
      </ul>
    </section>

    <footer class="footer">
      Generated with PMax Sentry Pro for {html.escape(agency_name)} &middot; Verified Read-Only Execution &middot; Strict Evidence Discipline
    </footer>
  </div>
</body>
</html>
"""

