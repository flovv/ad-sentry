from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from pmax_sentry_core.client import (
    GAQL_ASSET_GROUP_ASSETS,
    GAQL_ASSET_GROUP_SIGNALS,
    GAQL_ASSET_GROUPS,
    GAQL_CAMPAIGN_TOTALS,
    GAQL_SEARCH_TERM_INSIGHTS,
    GAQL_SEGMENTED_DELIVERY,
    GAQL_SHOPPING_PERFORMANCE,
    BaseGoogleAdsClient,
)
from pmax_sentry_core.models import (
    AccountInfo,
    AssetGroupAuditRow,
    AssetGroupHealthReport,
    CampaignInfo,
    DeliveryRow,
    ProductFeedAuditReport,
    SearchInsightRow,
    ZombieProductRow,
)

logger = logging.getLogger("pmax_sentry.live_client")


class GoogleAdsApiClient(BaseGoogleAdsClient):
    """
    Live Google Ads API client pinned to API v26.
    Connects to Google Ads API using official google-ads Python client library.
    """

    def __init__(
        self,
        config_path: Path | str | None = None,
        login_customer_id: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.config_path = Path(config_path) if config_path else None
        self.login_customer_id = login_customer_id.replace("-", "").strip() if login_customer_id else None

        if client is not None:
            self._client = client
        else:
            self._client = self._init_client()

    def _init_client(self) -> Any:
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            raise ImportError(
                "The 'google-ads' package is required for live API queries. "
                "Install it with `pip install pmax-sentry-core[google-ads]` or configure credentials."
            )

        if self.config_path and self.config_path.exists():
            return GoogleAdsClient.load_from_storage(path=str(self.config_path), version="v26")
        else:
            # Load from default environment / google-ads.yaml in user directory
            return GoogleAdsClient.load_from_storage(version="v26")

    def get_account_info(self, customer_id: str) -> AccountInfo:
        cid = customer_id.replace("-", "").strip()
        ga_service = self._client.get_service("GoogleAdsService", version="v26")
        query = """
        SELECT
          customer.id,
          customer.descriptive_name,
          customer.currency_code,
          customer.time_zone,
          customer.manager
        FROM customer
        LIMIT 1
        """
        response = ga_service.search(customer_id=cid, query=query)
        for row in response:
            return AccountInfo(
                customer_id=str(row.customer.id),
                descriptive_name=row.customer.descriptive_name or f"Account {cid}",
                currency_code=row.customer.currency_code or "USD",
                time_zone=row.customer.time_zone or "UTC",
                can_manage_clients=bool(row.customer.manager),
            )
        return AccountInfo(
            customer_id=cid,
            descriptive_name=f"Account {cid}",
            currency_code="USD",
            time_zone="UTC",
            can_manage_clients=False,
        )

    def list_pmax_campaigns(
        self, customer_id: str, include_demand_gen: bool = False
    ) -> list[CampaignInfo]:
        cid = customer_id.replace("-", "").strip()
        ga_service = self._client.get_service("GoogleAdsService", version="v26")
        channel_cond = (
            "IN ('PERFORMANCE_MAX', 'DEMAND_GEN')"
            if include_demand_gen
            else "= 'PERFORMANCE_MAX'"
        )
        query = f"""
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          campaign.advertising_channel_type,
          campaign.bidding_strategy_type,
          campaign.maximize_conversion_value.target_roas
        FROM campaign
        WHERE campaign.advertising_channel_type {channel_cond}
        ORDER BY campaign.id
        """
        response = ga_service.search(customer_id=cid, query=query)
        campaigns = []
        for row in response:
            camp = row.campaign
            status_name = camp.status.name if hasattr(camp.status, "name") else str(camp.status)
            channel_type_name = (
                camp.advertising_channel_type.name
                if hasattr(camp.advertising_channel_type, "name")
                else str(camp.advertising_channel_type)
            )
            strat_name = (
                camp.bidding_strategy_type.name
                if hasattr(camp.bidding_strategy_type, "name")
                else str(camp.bidding_strategy_type)
            )
            target_roas = (
                float(camp.maximize_conversion_value.target_roas)
                if hasattr(camp, "maximize_conversion_value") and camp.maximize_conversion_value.target_roas
                else None
            )
            campaigns.append(
                CampaignInfo(
                    id=str(camp.id),
                    name=camp.name,
                    status=status_name,
                    advertising_channel_type=channel_type_name,
                    bidding_strategy_type=strat_name,
                    target_roas=target_roas,
                )
            )
        return campaigns

    def query_unsegmented_totals(
        self, customer_id: str, start_date: date, end_date: date, include_demand_gen: bool = False
    ) -> int:
        cid = customer_id.replace("-", "").strip()
        ga_service = self._client.get_service("GoogleAdsService", version="v26")
        channel_cond = (
            "IN ('PERFORMANCE_MAX', 'DEMAND_GEN')"
            if include_demand_gen
            else "= 'PERFORMANCE_MAX'"
        )
        query = GAQL_CAMPAIGN_TOTALS.format(
            channel_types_condition=channel_cond,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        response = ga_service.search(customer_id=cid, query=query)
        total_cost_micros = 0
        for row in response:
            total_cost_micros += int(row.metrics.cost_micros)
        return total_cost_micros

    def query_segmented_delivery(
        self, customer_id: str, start_date: date, end_date: date, include_demand_gen: bool = False
    ) -> list[DeliveryRow]:
        cid = customer_id.replace("-", "").strip()
        account = self.get_account_info(cid)
        ga_service = self._client.get_service("GoogleAdsService", version="v26")
        channel_cond = (
            "IN ('PERFORMANCE_MAX', 'DEMAND_GEN')"
            if include_demand_gen
            else "= 'PERFORMANCE_MAX'"
        )
        query = GAQL_SEGMENTED_DELIVERY.format(
            channel_types_condition=channel_cond,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        response = ga_service.search(customer_id=cid, query=query)
        rows: list[DeliveryRow] = []

        for row in response:
            channel_val = (
                row.segments.ad_network_type.name
                if hasattr(row.segments.ad_network_type, "name")
                else str(row.segments.ad_network_type)
            )
            # Map enum representation to readable channel name
            channel_mapping = {
                "SEARCH": "Google Search",
                "SEARCH_PARTNERS": "Search Partners",
                "CONTENT": "Display",
                "YOUTUBE_WATCH": "YouTube",
                "YOUTUBE_SEARCH": "YouTube",
                "DISCOVER": "Discover",
                "GMAIL": "Gmail",
                "MAPS": "Maps",
            }
            clean_channel = channel_mapping.get(channel_val, channel_val.replace("_", " ").title())
            ad_channel_type = (
                row.campaign.advertising_channel_type.name
                if hasattr(row.campaign.advertising_channel_type, "name")
                else str(row.campaign.advertising_channel_type)
            )
            vt_conv = getattr(row.metrics, "view_through_conversions", 0)

            rows.append(
                DeliveryRow(
                    customer_id=cid,
                    campaign_id=str(row.campaign.id),
                    campaign_name=row.campaign.name,
                    advertising_channel_type=ad_channel_type,
                    date=date.fromisoformat(row.segments.date),
                    channel=clean_channel,
                    uses_product_data=getattr(row.segments, "ad_using_product_data", None),
                    uses_video=getattr(row.segments, "ad_using_video", None),
                    currency_code=account.currency_code,
                    cost_micros=int(row.metrics.cost_micros),
                    impressions=int(row.metrics.impressions),
                    clicks=int(row.metrics.clicks),
                    conversions=Decimal(str(row.metrics.conversions)),
                    conversion_value=Decimal(str(row.metrics.conversions_value)),
                    view_through_conversions=Decimal(str(vt_conv)),
                )
            )
        return rows

    def query_search_insights(
        self, customer_id: str, start_date: date, end_date: date
    ) -> list[SearchInsightRow]:
        cid = customer_id.replace("-", "").strip()
        ga_service = self._client.get_service("GoogleAdsService", version="v26")
        query = GAQL_SEARCH_TERM_INSIGHTS.format(
            start_date=start_date.isoformat(), end_date=end_date.isoformat()
        )
        response = ga_service.search(customer_id=cid, query=query)
        rows: list[SearchInsightRow] = []

        for row in response:
            rows.append(
                SearchInsightRow(
                    customer_id=cid,
                    campaign_id=str(row.campaign.id),
                    campaign_name=row.campaign.name,
                    category_label=row.campaign_search_term_insight.category_label,
                    date=date.fromisoformat(row.segments.date) if hasattr(row.segments, "date") and row.segments.date else None,
                    clicks=int(row.metrics.clicks),
                    conversions=Decimal(str(row.metrics.conversions)),
                    conversion_value=Decimal(str(row.metrics.conversions_value)),
                    impressions=int(row.metrics.impressions),
                    search_volume=int(row.metrics.search_volume) if hasattr(row.metrics, "search_volume") and row.metrics.search_volume else None,
                )
            )
        return rows

    def query_asset_groups(self, customer_id: str) -> AssetGroupHealthReport:
        """Fetch and audit live PMax asset groups, assets, and signals via GAQL."""
        cid = customer_id.replace("-", "").strip()
        ga_service = self._client.get_service("GoogleAdsService", version=self.api_version)

        ag_meta: dict[str, dict[str, Any]] = {}
        for row in ga_service.search(customer_id=cid, query=GAQL_ASSET_GROUPS):
            ag = row.asset_group
            ag_id = str(ag.id)
            status_name = ag.status.name if hasattr(ag.status, "name") else str(ag.status)
            ad_strength = ag.ad_strength.name if hasattr(ag.ad_strength, "name") else str(ag.ad_strength)
            ag_meta[ag_id] = {
                "asset_group_id": ag_id,
                "asset_group_name": ag.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "status": status_name,
                "ad_strength": ad_strength,
                "headlines": 0,
                "long_headlines": 0,
                "descriptions": 0,
                "images": 0,
                "has_square": False,
                "has_landscape": False,
                "has_portrait": False,
                "videos": 0,
                "has_vertical_video": False,
                "search_themes": 0,
                "has_audience_signals": False,
            }

        if not ag_meta:
            return AssetGroupHealthReport()

        for row in ga_service.search(customer_id=cid, query=GAQL_ASSET_GROUP_ASSETS):
            ag_id = str(row.asset_group.id)
            if ag_id not in ag_meta:
                continue
            entry = ag_meta[ag_id]
            ft = (
                row.asset_group_asset.field_type.name
                if hasattr(row.asset_group_asset.field_type, "name")
                else str(row.asset_group_asset.field_type)
            )
            if ft == "HEADLINE":
                entry["headlines"] += 1
            elif ft == "LONG_HEADLINE":
                entry["long_headlines"] += 1
            elif ft == "DESCRIPTION":
                entry["descriptions"] += 1
            elif ft in ("MARKETING_IMAGE", "SQUARE_MARKETING_IMAGE", "PORTRAIT_MARKETING_IMAGE"):
                entry["images"] += 1
                if ft == "SQUARE_MARKETING_IMAGE":
                    entry["has_square"] = True
                elif ft == "MARKETING_IMAGE":
                    entry["has_landscape"] = True
                elif ft == "PORTRAIT_MARKETING_IMAGE":
                    entry["has_portrait"] = True
            elif ft in ("YOUTUBE_VIDEO", "PORTRAIT_VIDEO"):
                entry["videos"] += 1
                if ft == "PORTRAIT_VIDEO":
                    entry["has_vertical_video"] = True

        try:
            for row in ga_service.search(customer_id=cid, query=GAQL_ASSET_GROUP_SIGNALS):
                ag_id = str(row.asset_group.id)
                if ag_id not in ag_meta:
                    continue
                sig = row.asset_group_signal
                if hasattr(sig, "audience") and getattr(sig.audience, "audience", None):
                    ag_meta[ag_id]["has_audience_signals"] = True
                if hasattr(sig, "search_theme") and getattr(sig.search_theme, "text", None):
                    ag_meta[ag_id]["search_themes"] += 1
        except Exception as exc:
            logger.warning("Could not query asset_group_signal for %s: %s", cid, exc)

        audited: list[AssetGroupAuditRow] = []
        for entry in ag_meta.values():
            score = 0
            critical_issues: list[str] = []
            action_items: list[str] = []

            if entry["headlines"] >= 5:
                score += 15
            elif entry["headlines"] >= 3:
                score += 8
                critical_issues.append(f"Headlines below best-practice threshold ({entry['headlines']}/5 minimum)")
                action_items.append("Add distinct value-proposition headlines to reach at least 5.")
            else:
                critical_issues.append(f"Critically low headline count ({entry['headlines']}/5 minimum)")
                action_items.append("Upload at least 5 headlines immediately.")

            if entry["long_headlines"] >= 2:
                score += 10
            elif entry["long_headlines"] == 1:
                score += 5
                action_items.append("Add a second long headline for Display/Discover variation.")
            else:
                critical_issues.append("Missing long headlines (0 uploaded)")

            if entry["descriptions"] >= 3:
                score += 10
            elif entry["descriptions"] >= 1:
                score += 5
                action_items.append("Add descriptions to reach at least 3.")
            else:
                critical_issues.append("Missing descriptions (0 uploaded)")

            if entry["has_square"]:
                score += 10
            else:
                critical_issues.append("Missing 1:1 square image (limiting Display network formats)")
                action_items.append("Upload 1:1 square marketing images.")

            if entry["has_landscape"]:
                score += 10
            else:
                critical_issues.append("Missing 1.91:1 landscape image")
                action_items.append("Upload 1.91:1 landscape marketing images.")

            if entry["has_portrait"]:
                score += 5
            if entry["images"] >= 5:
                score += 5

            if entry["videos"] >= 1:
                score += 10
            else:
                critical_issues.append("Zero video assets uploaded (forfeiting YouTube and Shorts delivery)")
                action_items.append("Upload native video creatives to avoid low-quality auto-generated slideshows.")

            if entry["has_vertical_video"]:
                score += 10
            elif entry["videos"] >= 1:
                critical_issues.append("Missing 9:16 Vertical Video (Google auto-generates slideshow video on Shorts)")
                action_items.append("Upload a native 9:16 vertical video for YouTube Shorts.")

            if entry["has_audience_signals"]:
                score += 10
            else:
                critical_issues.append("Missing audience signals (algorithm exploring broadly without seed targets)")
                action_items.append("Attach Customer Match or Custom In-Market audience signals.")

            if entry["search_themes"] >= 3:
                score += 5
            elif entry["search_themes"] >= 1:
                score += 3
            else:
                action_items.append("Add Search Themes to guide PMax Search inventory discovery.")

            if not action_items:
                action_items.append("Asset coverage is optimal. Monitor search theme match rate and creative fatigue.")

            grade = (
                "A+" if score >= 93
                else "A" if score >= 85
                else "B" if score >= 75
                else "C" if score >= 60
                else "D" if score >= 45
                else "F"
            )

            audited.append(
                AssetGroupAuditRow(
                    asset_group_id=entry["asset_group_id"],
                    asset_group_name=entry["asset_group_name"],
                    campaign_id=entry["campaign_id"],
                    campaign_name=entry["campaign_name"],
                    status=entry["status"],
                    ad_strength=entry["ad_strength"],
                    headlines_count=entry["headlines"],
                    long_headlines_count=entry["long_headlines"],
                    descriptions_count=entry["descriptions"],
                    images_count=entry["images"],
                    has_square_image=entry["has_square"],
                    has_landscape_image=entry["has_landscape"],
                    has_portrait_image=entry["has_portrait"],
                    videos_count=entry["videos"],
                    has_vertical_video=entry["has_vertical_video"],
                    search_themes_count=entry["search_themes"],
                    has_audience_signals=entry["has_audience_signals"],
                    score=score,
                    grade=grade,
                    critical_issues=critical_issues,
                    action_items=action_items,
                )
            )

        avg_score = round(sum(g.score for g in audited) / len(audited), 1)
        overall_grade = (
            "A" if avg_score >= 90
            else "B" if avg_score >= 80
            else "C" if avg_score >= 65
            else "D" if avg_score >= 50
            else "F"
        )
        missing_vert = sum(1 for g in audited if not g.has_vertical_video)
        missing_aud = sum(1 for g in audited if not g.has_audience_signals)
        recs: list[str] = []
        if missing_vert > 0:
            recs.append(f"Upload 9:16 vertical videos across {missing_vert} asset group(s) to eliminate auto-generated Shorts.")
        if missing_aud > 0:
            recs.append(f"Attach audience signal seeds to {missing_aud} asset group(s) to stop broad algorithm wandering.")

        return AssetGroupHealthReport(
            total_asset_groups=len(audited),
            average_score=avg_score,
            overall_grade=overall_grade,
            missing_vertical_video_count=missing_vert,
            missing_audience_signals_count=missing_aud,
            asset_groups=audited,
            recommendations=recs,
        )

    def query_product_feed(
        self, customer_id: str, start_date: date, end_date: date
    ) -> ProductFeedAuditReport:
        """Fetch and audit live Google Merchant Center product feed performance via GAQL."""
        cid = customer_id.replace("-", "").strip()
        ga_service = self._client.get_service("GoogleAdsService", version=self.api_version)
        query = GAQL_SHOPPING_PERFORMANCE.format(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        sku_agg: dict[str, dict[str, Any]] = {}
        for row in ga_service.search(customer_id=cid, query=query):
            sku_id = str(getattr(row.segments, "product_item_id", "") or "unknown_sku")
            title = str(getattr(row.segments, "product_title", "") or sku_id)
            brand = str(getattr(row.segments, "product_brand", "") or "Unknown")
            cost = Decimal(int(row.metrics.cost_micros)) / Decimal(1_000_000)
            imps = int(row.metrics.impressions)
            clicks = int(row.metrics.clicks)
            convs = Decimal(str(row.metrics.conversions))
            cval = Decimal(str(row.metrics.conversions_value))

            if sku_id not in sku_agg:
                sku_agg[sku_id] = {
                    "product_id": sku_id,
                    "title": title,
                    "brand": brand,
                    "cost": Decimal("0"),
                    "impressions": 0,
                    "clicks": 0,
                    "conversions": Decimal("0"),
                    "conversion_value": Decimal("0"),
                }
            rec = sku_agg[sku_id]
            rec["cost"] += cost
            rec["impressions"] += imps
            rec["clicks"] += clicks
            rec["conversions"] += convs
            rec["conversion_value"] += cval

        if not sku_agg:
            return ProductFeedAuditReport()

        zombies: list[ZombieProductRow] = []
        top_performers_count = 0
        ghost_count = 0
        total_cost = Decimal("0")
        zombie_spend = Decimal("0")

        for rec in sku_agg.values():
            cost = rec["cost"].quantize(Decimal("0.01"))
            total_cost += cost
            if rec["conversions"] > 0:
                top_performers_count += 1
            elif cost > 0:
                zombie_spend += cost
                zombies.append(
                    ZombieProductRow(
                        product_id=rec["product_id"],
                        title=rec["title"],
                        brand=rec["brand"],
                        cost=cost,
                        impressions=rec["impressions"],
                        clicks=rec["clicks"],
                        conversions=rec["conversions"],
                        conversion_value=rec["conversion_value"].quantize(Decimal("0.01")),
                        classification="ZOMBIE",
                        suggested_action=(
                            f"Exclude SKU or set Custom Label 0 = 'zombie' to halt {cost:,.2f} zero-conversion spend."
                        ),
                    )
                )
            else:
                ghost_count += 1

        zombies.sort(key=lambda z: z.cost, reverse=True)
        day_count = max(1, (end_date - start_date).days + 1)
        zombie_share = (
            ((zombie_spend / total_cost) * Decimal(100)).quantize(Decimal("0.1"))
            if total_cost > 0
            else Decimal("0.0")
        )
        est_monthly = (zombie_spend * Decimal(30) / Decimal(day_count)).quantize(Decimal("0.01"))

        action_plan: list[str] = []
        if zombies:
            action_plan.append(
                f"Exclude or deprioritize {len(zombies)} Zombie SKUs to recover ~{est_monthly:,.2f}/mo ({zombie_share}% of feed spend)."
            )
        if top_performers_count > 0:
            action_plan.append(
                f"Reallocate recovered budget into {top_performers_count} converting SKUs currently constrained by target ROAS bids."
            )
        if ghost_count > 0:
            action_plan.append(
                f"Review {ghost_count} Ghost SKUs (0 spend) for Merchant Center disapprovals or under-competitive bids."
            )

        return ProductFeedAuditReport(
            total_products_audited=len(sku_agg),
            total_feed_cost=total_cost.quantize(Decimal("0.01")),
            zombie_products_count=len(zombies),
            zombie_spend=zombie_spend.quantize(Decimal("0.01")),
            zombie_spend_share=zombie_share,
            top_performers_count=top_performers_count,
            ghost_products_count=ghost_count,
            top_zombie_products=zombies[:20],
            estimated_monthly_savings=est_monthly,
            action_plan=action_plan,
        )
