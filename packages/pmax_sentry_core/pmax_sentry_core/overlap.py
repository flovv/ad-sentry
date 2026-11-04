from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from pmax_sentry_core.models import CrossCampaignOverlapSummary, DeliveryRow


def calculate_cross_campaign_overlap(
    rows: Sequence[DeliveryRow],
) -> CrossCampaignOverlapSummary | None:
    """
    Analyzes cross-campaign delivery between Performance Max and Demand Gen.
    Detects inventory collision across shared surfaces (YouTube, Discover, Gmail)
    and deconstructs click vs. view-through conversion ratios.
    """
    pmax_rows = [r for r in rows if r.advertising_channel_type == "PERFORMANCE_MAX"]
    dg_rows = [r for r in rows if r.advertising_channel_type == "DEMAND_GEN"]

    if not dg_rows:
        return None

    pmax_cost = sum((r.cost for r in pmax_rows), Decimal(0))
    dg_cost = sum((r.cost for r in dg_rows), Decimal(0))
    total_cost = pmax_cost + dg_cost

    shared_surfaces = ["YouTube", "Discover", "Gmail"]
    all_channels = sorted(list({r.channel for r in rows}))

    surface_breakdown = []
    shared_pmax_spend = Decimal(0)
    shared_dg_spend = Decimal(0)

    for ch in all_channels:
        p_spend = sum((r.cost for r in pmax_rows if r.channel == ch), Decimal(0))
        d_spend = sum((r.cost for r in dg_rows if r.channel == ch), Decimal(0))
        surface_total = p_spend + d_spend
        is_shared = ch in shared_surfaces and p_spend > 0 and d_spend > 0

        if ch in shared_surfaces:
            shared_pmax_spend += p_spend
            shared_dg_spend += d_spend

        surface_breakdown.append(
            {
                "channel": ch,
                "pmax_spend": float(p_spend),
                "demand_gen_spend": float(d_spend),
                "total_spend": float(surface_total),
                "is_shared": is_shared,
                "pmax_share": float((p_spend / pmax_cost * 100) if pmax_cost > 0 else 0),
                "demand_gen_share": float((d_spend / dg_cost * 100) if dg_cost > 0 else 0),
            }
        )

    shared_total = shared_pmax_spend + shared_dg_spend
    if shared_total > 0 and shared_dg_spend > 0 and shared_pmax_spend > 0:
        dg_ratio = shared_dg_spend / shared_total
        if dg_ratio >= Decimal("0.25"):
            severity = "HIGH"
        elif dg_ratio >= Decimal("0.10"):
            severity = "MEDIUM"
        else:
            severity = "LOW"
    else:
        severity = "NONE"

    # View-Through Conversion Ratios
    pmax_conversions = sum((r.conversions for r in pmax_rows), Decimal(0))
    pmax_vt = sum((r.view_through_conversions for r in pmax_rows), Decimal(0))
    pmax_total_attr = pmax_conversions + pmax_vt
    pmax_vt_ratio = (pmax_vt / pmax_total_attr) if pmax_total_attr > 0 else Decimal(0)

    dg_conversions = sum((r.conversions for r in dg_rows), Decimal(0))
    dg_vt = sum((r.view_through_conversions for r in dg_rows), Decimal(0))
    dg_total_attr = dg_conversions + dg_vt
    dg_vt_ratio = (dg_vt / dg_total_attr) if dg_total_attr > 0 else Decimal(0)

    recommendations = []
    if severity in ("HIGH", "MEDIUM"):
        recommendations.append(
            f"High auction collision detected on shared surfaces ({', '.join(shared_surfaces)}). "
            f"Demand Gen accounts for {float(shared_dg_spend):,.2f} while PMax spends {float(shared_pmax_spend):,.2f} on identical placements."
        )
        recommendations.append(
            "Asset Specialization: Remove video assets from PMax to restrict it to a Feed-Only Shopping engine, delegating video storytelling exclusively to Demand Gen."
        )
    if dg_vt_ratio > Decimal("0.35"):
        recommendations.append(
            f"Demand Gen conversion reporting has a high View-Through/Engaged-View share ({float(dg_vt_ratio * 100):.1f}%). "
            "High risk of double-attribution with subsequent PMax Search or direct brand conversions."
        )
    recommendations.append(
        "Audience Hygiene: Add Customer Match and 90-day site visitors as exclusions in Demand Gen to prevent bidding on warm audiences already captured in PMax."
    )

    return CrossCampaignOverlapSummary(
        pmax_cost=pmax_cost,
        demand_gen_cost=dg_cost,
        total_cost=total_cost,
        shared_surfaces=shared_surfaces,
        surface_breakdown=surface_breakdown,
        overlap_severity=severity,
        pmax_view_through_ratio=pmax_vt_ratio.quantize(Decimal("0.0001")),
        demand_gen_view_through_ratio=dg_vt_ratio.quantize(Decimal("0.0001")),
        recommendations=recommendations,
    )
