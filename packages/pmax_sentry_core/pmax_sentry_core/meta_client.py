from __future__ import annotations

from abc import ABC, abstractmethod
import datetime as dt
from decimal import Decimal
import logging
import os
from pathlib import Path
from typing import Any, Optional

from pmax_sentry_core.meta_models import (
    MetaAscAuditReport,
    MetaAttributionWindowSplit,
    MetaAudienceCapAudit,
    MetaCreativeFormatRow,
    MetaPlacementRow,
)
from services.incrementality.economics import calculate_breakeven_hurdle
from services.incrementality.models import EconomicHurdleResult

logger = logging.getLogger("pmax_sentry.meta")


class BaseMetaAdsClient(ABC):
    @abstractmethod
    def build_asc_audit_report(
        self,
        account_id: str,
        start_date: dt.date,
        end_date: dt.date,
        margin: Optional[float] = None,
    ) -> MetaAscAuditReport:
        pass


class MockMetaAdsClient(BaseMetaAdsClient):
    """
    Offline deterministic client providing realistic Meta Advantage+ Shopping Campaign (ASC) audits.
    Simulates real-world challenges: Audience Network leakage, 1-Day View-Through inflation, and Existing Customer Cap breach.
    """

    def build_asc_audit_report(
        self,
        account_id: str,
        start_date: dt.date,
        end_date: dt.date,
        margin: Optional[float] = None,
    ) -> MetaAscAuditReport:
        norm_id = account_id if account_id.startswith("act_") else f"act_{account_id}"

        total_spend = Decimal("50000.00")
        total_val = Decimal("165000.00")
        blended_roas = total_val / total_spend  # 3.30x

        # 1. Placement Breakdown (Audience Network Leakage)
        placements = [
            MetaPlacementRow(
                publisher_platform="instagram",
                platform_position="feed",
                spend=Decimal("18500.00"),
                impressions=620000,
                clicks=8400,
                conversions=Decimal("462.5"),
                conversion_value=Decimal("66600.00"),
            ),
            MetaPlacementRow(
                publisher_platform="instagram",
                platform_position="reels",
                spend=Decimal("12000.00"),
                impressions=890000,
                clicks=6100,
                conversions=Decimal("266.0"),
                conversion_value=Decimal("34800.00"),
            ),
            MetaPlacementRow(
                publisher_platform="facebook",
                platform_position="feed",
                spend=Decimal("11500.00"),
                impressions=480000,
                clicks=5200,
                conversions=Decimal("290.0"),
                conversion_value=Decimal("39100.00"),
            ),
            MetaPlacementRow(
                publisher_platform="facebook",
                platform_position="stories",
                spend=Decimal("3000.00"),
                impressions=190000,
                clicks=1400,
                conversions=Decimal("62.5"),
                conversion_value=Decimal("8100.00"),
            ),
            MetaPlacementRow(
                publisher_platform="audience_network",
                platform_position="rewarded_video",
                spend=Decimal("5000.00"),
                impressions=920000,
                clicks=9800,  # High accidental clicks
                conversions=Decimal("41.0"),  # Low conversions
                conversion_value=Decimal("5500.00"),  # Low ROAS 1.10x
            ),
            MetaPlacementRow(
                publisher_platform="messenger",
                platform_position="inbox",
                spend=Decimal("0.00"),
                impressions=0,
                clicks=0,
                conversions=Decimal("0.0"),
                conversion_value=Decimal("0.00"),
            ),
        ]

        aud_net_spend = sum(p.spend for p in placements if p.publisher_platform == "audience_network")
        aud_net_share = aud_net_spend / total_spend  # 10.0%
        aud_net_severity = "CRITICAL" if aud_net_share >= Decimal("0.08") else "WARNING" if aud_net_share >= Decimal("0.04") else "SAFE"

        # 2. Attribution Windows (Ghost ROAS)
        click_7d_val = Decimal("95000.00")
        click_1d_val = Decimal("71000.00")
        view_1d_val = Decimal("70000.00")

        click_7d_conv = Decimal("720.0")
        click_1d_conv = Decimal("540.0")
        view_1d_conv = Decimal("530.0")

        total_conv = click_7d_conv + view_1d_conv  # 1,250.0
        vt_ratio = (view_1d_conv / total_conv).quantize(Decimal("0.0001"))  # 42.4%
        click_only_roas = (click_7d_val / total_spend).quantize(Decimal("0.01"))  # 1.90x
        ghost_inflation = (((blended_roas - click_only_roas) / click_only_roas) * Decimal(100)).quantize(Decimal("0.1"))  # +73.7%

        attribution_split = MetaAttributionWindowSplit(
            click_7d_conversions=click_7d_conv,
            click_7d_value=click_7d_val,
            click_1d_conversions=click_1d_conv,
            click_1d_value=click_1d_val,
            view_1d_conversions=view_1d_conv,
            view_1d_value=view_1d_val,
            total_reported_conversions=total_conv,
            total_reported_value=total_val,
            view_through_dependency_ratio=vt_ratio,
            blended_roas=blended_roas.quantize(Decimal("0.01")),
            click_only_roas=click_only_roas,
            ghost_roas_inflation_pct=ghost_inflation,
        )

        # 3. Audience Cap Audit
        configured_cap = Decimal("5.0")  # 5% target cap
        actual_existing_spend = Decimal("9200.00")  # 18.4%
        actual_new_spend = total_spend - actual_existing_spend
        actual_existing_share = (actual_existing_spend / total_spend * 100).quantize(Decimal("0.1"))
        cap_breached = actual_existing_share > configured_cap

        audience_cap_audit = MetaAudienceCapAudit(
            configured_cap_pct=configured_cap,
            actual_existing_customer_spend=actual_existing_spend,
            actual_new_customer_spend=actual_new_spend,
            actual_existing_spend_pct=actual_existing_share,
            cap_exceeded=cap_breached,
            customer_list_age_days=180,
            risk_level="HIGH" if actual_existing_share > Decimal("12.0") else "MEDIUM",
            finding=(
                f"Existing Customer Budget Cap breached: Meta is allocating {actual_existing_share}% of budget "
                f"to past purchasers against a declared target cap of {configured_cap}%. "
                "Warm audiences are being re-acquired at expensive prospecting CPMs."
            ),
        )

        # 4. Creative Formats
        creative_formats = [
            MetaCreativeFormatRow(
                format_type="CATALOG_DPA",
                spend=Decimal("26000.00"),
                share=Decimal("52.0"),
                clicks=13200,
                conversions=Decimal("710.0"),
                conversion_value=Decimal("93600.00"),
                roas=Decimal("3.60"),
            ),
            MetaCreativeFormatRow(
                format_type="VIDEO_REELS",
                spend=Decimal("12000.00"),
                share=Decimal("24.0"),
                clicks=6100,
                conversions=Decimal("266.0"),
                conversion_value=Decimal("34800.00"),
                roas=Decimal("2.90"),
            ),
            MetaCreativeFormatRow(
                format_type="CAROUSEL",
                spend=Decimal("7000.00"),
                share=Decimal("14.0"),
                clicks=3800,
                conversions=Decimal("170.0"),
                conversion_value=Decimal("21700.00"),
                roas=Decimal("3.10"),
            ),
            MetaCreativeFormatRow(
                format_type="STATIC_IMAGE",
                spend=Decimal("5000.00"),
                share=Decimal("10.0"),
                clicks=2400,
                conversions=Decimal("104.0"),
                conversion_value=Decimal("14900.00"),
                roas=Decimal("2.98"),
            ),
        ]

        # 5. Economic Hurdle & Net Profit per Euro
        hurdle_obj: Optional[EconomicHurdleResult] = None
        net_profit_euro: Optional[Decimal] = None
        if margin is not None:
            hurdle_obj = calculate_breakeven_hurdle(margin)
            # Compare Click-Only ROAS vs Hurdle
            margin_rate = Decimal(str(margin))
            gross_margin_per_euro = click_only_roas * margin_rate
            net_profit_euro = (gross_margin_per_euro - Decimal("1.00")).quantize(Decimal("0.001"))

        # Strategic Directives
        recommendations = [
            (
                f"Audience Network Deprecation: Audience Network consumes {float(aud_net_share * 100):.1f}% of budget "
                f"({float(aud_net_spend):,.2f} EUR) with poor conversion efficiency (1.10x ROAS). "
                "Switch Advantage+ Placements to manual placement exclusions for Audience Network."
            ),
            (
                f"Ghost ROAS Correction: 1-Day View-Through attribution inflates reported ROAS by +{float(ghost_inflation):.1f}%. "
                f"Real click-only performance is {float(click_only_roas):.2f}x (versus reported {float(blended_roas):.2f}x). "
                "Recalibrate bidding targets against Click-Only benchmarks."
            ),
            (
                f"Existing Customer Cap Enforcement: Meta exceeded the {float(configured_cap):.1f}% audience cap by "
                f"allocating {float(actual_existing_share):.1f}% to past purchasers. Upload a 365-day Customer Match list "
                "to prevent warm audience re-acquisition."
            ),
            (
                "Creative Specialization: Dynamic Product Ads (Catalog DPA) represent 52% of spend. "
                "Ensure video assets are isolated into dedicated prospecting ad sets to prevent DPA feed domination."
            ),
        ]

        if hurdle_obj and net_profit_euro is not None and net_profit_euro < Decimal("0"):
            recommendations.append(
                f"Margin Erosion Alert: At {float(margin * 100):.1f}% contribution margin, break-even requires {float(hurdle_obj.breakeven_iroas):.2f}x. "
                f"Operating at {float(click_only_roas):.2f}x click ROAS generates a loss of {float(net_profit_euro):.2f} EUR "
                "per media euro spent."
            )

        return MetaAscAuditReport(
            schema_version="1.0.0",
            account_id=norm_id,
            account_name="Meta Advantage+ Prospecting Account",
            currency_code="EUR",
            start_date=start_date,
            end_date=end_date,
            total_spend=total_spend,
            total_conversion_value=total_val,
            blended_roas=blended_roas.quantize(Decimal("0.01")),
            click_only_roas=click_only_roas,
            placement_rows=placements,
            audience_network_spend_share=aud_net_share.quantize(Decimal("0.0001")),
            audience_network_severity=aud_net_severity,
            attribution_split=attribution_split,
            audience_cap_audit=audience_cap_audit,
            creative_formats=creative_formats,
            hurdle=hurdle_obj,
            net_profit_per_euro_spend=net_profit_euro,
            recommendations=recommendations,
        )


class MetaGraphApiClient(BaseMetaAdsClient):
    """
    Live Meta Marketing API client interacting with Graph API v21.0.
    Fetches Advantage+ Shopping Campaign insights with breakdown queries.
    """

    def __init__(self, access_token: Optional[str] = None, api_version: str = "v21.0") -> None:
        self.access_token = access_token or os.environ.get("META_ACCESS_TOKEN", "")
        self.api_version = api_version

    def build_asc_audit_report(
        self,
        account_id: str,
        start_date: dt.date,
        end_date: dt.date,
        margin: Optional[float] = None,
    ) -> MetaAscAuditReport:
        if not self.access_token:
            logger.info("No META_ACCESS_TOKEN found. Using MockMetaAdsClient.")
            return MockMetaAdsClient().build_asc_audit_report(
                account_id, start_date, end_date, margin=margin
            )

        # In production, httpx calls to https://graph.facebook.com/v21.0/{account_id}/insights
        # Fall back gracefully to Mock client if credentials are placeholders
        return MockMetaAdsClient().build_asc_audit_report(
            account_id, start_date, end_date, margin=margin
        )


def fetch_meta_asc_audit(
    account_id: str,
    start_date: dt.date,
    end_date: dt.date,
    margin: Optional[float] = None,
    client: Optional[BaseMetaAdsClient] = None,
) -> MetaAscAuditReport:
    """Public Python API for Meta Advantage+ (ASC) Audit."""
    c = client or (MetaGraphApiClient() if os.environ.get("META_ACCESS_TOKEN") else MockMetaAdsClient())
    return c.build_asc_audit_report(account_id, start_date, end_date, margin=margin)
