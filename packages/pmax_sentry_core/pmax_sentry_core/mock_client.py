from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import random

from pmax_sentry_core.client import BaseGoogleAdsClient
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


class MockGoogleAdsClient(BaseGoogleAdsClient):
    """
    Offline/testing client that returns deterministic, spec-compliant data.
    Provides realistic PMax delivery distributions across Google Search, Search Partners,
    Display, YouTube, Discover, Gmail, and Maps with separate format flags.
    """

    def __init__(self, partial_coverage: bool = False, discrepancy_micros: int = 0) -> None:
        self.partial_coverage = partial_coverage
        self.discrepancy_micros = discrepancy_micros

    def get_account_info(self, customer_id: str) -> AccountInfo:
        cid = customer_id.replace("-", "").strip()
        if cid.startswith("2"):
            return AccountInfo(
                customer_id=cid,
                descriptive_name="Acme SaaS Europe",
                currency_code="EUR",
                time_zone="Europe/Berlin",
                can_manage_clients=False,
            )
        elif cid.startswith("3"):
            return AccountInfo(
                customer_id=cid,
                descriptive_name="British Retail Ltd",
                currency_code="GBP",
                time_zone="Europe/London",
                can_manage_clients=False,
            )
        elif cid.startswith("4"):
            return AccountInfo(
                customer_id=cid,
                descriptive_name="Zero Spend Inc",
                currency_code="USD",
                time_zone="America/Los_Angeles",
                can_manage_clients=False,
            )
        return AccountInfo(
            customer_id=cid,
            descriptive_name="Northwind Commerce US",
            currency_code="USD",
            time_zone="America/New_York",
            can_manage_clients=False,
        )

    def list_pmax_campaigns(
        self, customer_id: str, include_demand_gen: bool = False
    ) -> list[CampaignInfo]:
        cid = customer_id.replace("-", "").strip()
        if cid.startswith("4"):
            return [
                CampaignInfo(
                    id="90001",
                    name="PMax - Dormant Brand",
                    status="PAUSED",
                    advertising_channel_type="PERFORMANCE_MAX",
                    bidding_strategy_type="MAXIMIZE_CONVERSION_VALUE",
                    target_roas=3.0,
                )
            ]
        base_campaigns = [
            CampaignInfo(
                id="10001",
                name="PMax - Core Product Feed",
                status="ENABLED",
                advertising_channel_type="PERFORMANCE_MAX",
                bidding_strategy_type="MAXIMIZE_CONVERSION_VALUE",
                target_roas=3.5,
            ),
            CampaignInfo(
                id="10002",
                name="PMax - High Margin Assets",
                status="ENABLED",
                advertising_channel_type="PERFORMANCE_MAX",
                bidding_strategy_type="MAXIMIZE_CONVERSION_VALUE",
                target_roas=4.0,
            ),
            CampaignInfo(
                id="10003",
                name="PMax - Seasonal Test (Q3)",
                status="PAUSED",
                advertising_channel_type="PERFORMANCE_MAX",
                bidding_strategy_type="MAXIMIZE_CONVERSIONS",
                target_roas=None,
            ),
        ]
        if include_demand_gen:
            base_campaigns.append(
                CampaignInfo(
                    id="20001",
                    name="Demand Gen - Video & Shorts Prospecting",
                    status="ENABLED",
                    advertising_channel_type="DEMAND_GEN",
                    bidding_strategy_type="MAXIMIZE_CONVERSIONS",
                    target_roas=2.0,
                )
            )
        return base_campaigns

    def query_segmented_delivery(
        self, customer_id: str, start_date: date, end_date: date, include_demand_gen: bool = False
    ) -> list[DeliveryRow]:
        cid = customer_id.replace("-", "").strip()
        if cid.startswith("4"):
            return []

        account = self.get_account_info(cid)
        campaigns = [
            c for c in self.list_pmax_campaigns(cid, include_demand_gen=include_demand_gen) if c.status == "ENABLED"
        ]
        rows: list[DeliveryRow] = []

        # PMax Channel & format combinations
        pmax_segments_profile = [
            ("Google Search", True, False, 0.35, 3.8),     # 35% spend, roas ~ 3.8
            ("Google Search", False, False, 0.10, 3.2),    # 10% spend
            ("Search Partners", False, False, 0.05, 2.1),  # 5% spend
            ("YouTube", False, True, 0.15, 1.8),           # 15% spend
            ("YouTube", True, True, 0.05, 2.4),            # 5% spend
            ("Display", True, False, 0.15, 1.5),           # 15% spend
            ("Display", False, False, 0.05, 1.2),          # 5% spend
            ("Discover", True, False, 0.05, 2.6),          # 5% spend
            ("Gmail", True, False, 0.05, 2.2),             # 5% spend
        ]

        # Demand Gen Channel & format combinations (YouTube, Discover, Gmail)
        demand_gen_profile = [
            ("YouTube", False, True, 0.55, 1.4),           # 55% spend on YouTube / Shorts
            ("Discover", True, False, 0.30, 2.1),          # 30% spend on Discover
            ("Gmail", False, False, 0.15, 1.7),            # 15% spend on Gmail
        ]

        curr_date = start_date
        day_count = (end_date - start_date).days + 1
        base_daily_spend_micros = 1_200_000_000 // max(1, day_count)  # ~$1200 total spend across period

        while curr_date <= end_date:
            day_seed = curr_date.toordinal()
            rng = random.Random(day_seed + int(cid[:5]))

            for camp in campaigns:
                is_dg = camp.advertising_channel_type == "DEMAND_GEN"
                segments_profile = demand_gen_profile if is_dg else pmax_segments_profile
                camp_spend_weight = 0.35 if is_dg else (0.65 / max(1, len(campaigns) - 1))

                for channel, uses_prod, uses_vid, spend_share, target_roas in segments_profile:
                    daily_micros = int(base_daily_spend_micros * camp_spend_weight * spend_share)
                    variation = 0.9 + (rng.random() * 0.2)
                    cost_micros = int(daily_micros * variation)

                    if cost_micros <= 0:
                        continue

                    cpc_micros = int(1_200_000 if "Search" in channel else 350_000)
                    clicks = max(1, cost_micros // cpc_micros)
                    ctr = 0.06 if "Search" in channel else 0.015
                    impressions = max(clicks, int(clicks / ctr))

                    cvr = 0.035 if "Search" in channel else 0.012
                    conversions = Decimal(str(round(clicks * cvr, 2)))

                    # Demand Gen has high view-through conversion ratio (EVC/VT) vs PMax
                    if is_dg:
                        vt_conversions = (conversions * Decimal("1.55")).quantize(Decimal("0.01"))
                    else:
                        vt_conversions = (conversions * Decimal("0.08")).quantize(Decimal("0.01"))

                    spend_units = Decimal(cost_micros) / Decimal(1_000_000)
                    conv_val = (spend_units * Decimal(str(target_roas)) * Decimal(str(variation))).quantize(Decimal("0.01"))

                    rows.append(
                        DeliveryRow(
                            customer_id=cid,
                            campaign_id=camp.id,
                            campaign_name=camp.name,
                            advertising_channel_type=camp.advertising_channel_type,
                            date=curr_date,
                            channel=channel,
                            uses_product_data=uses_prod,
                            uses_video=uses_vid,
                            currency_code=account.currency_code,
                            cost_micros=cost_micros,
                            impressions=impressions,
                            clicks=clicks,
                            conversions=conversions,
                            conversion_value=conv_val,
                            view_through_conversions=vt_conversions,
                        )
                    )
            curr_date += timedelta(days=1)

        return rows

    def query_unsegmented_totals(
        self, customer_id: str, start_date: date, end_date: date, include_demand_gen: bool = False
    ) -> int:
        segmented_rows = self.query_segmented_delivery(
            customer_id, start_date, end_date, include_demand_gen=include_demand_gen
        )
        segmented_total = sum(r.cost_micros for r in segmented_rows)

        if segmented_total == 0:
            return 0

        cid = customer_id.replace("-", "").strip()
        # If client was explicitly configured with discrepancy, use it
        if self.discrepancy_micros != 0:
            return segmented_total + self.discrepancy_micros

        if self.partial_coverage or cid.startswith("3"):
            # British Retail Ltd has 8.5% unexplained difference in total vs segmented reporting
            return int(segmented_total * 1.085)

        # By default, totals reconcile exactly
        return segmented_total

    def query_search_insights(
        self, customer_id: str, start_date: date, end_date: date
    ) -> list[SearchInsightRow]:
        cid = customer_id.replace("-", "").strip()
        if cid.startswith("4"):
            return []

        campaigns = [c for c in self.list_pmax_campaigns(cid) if c.status == "ENABLED"]
        categories = [
            ("brand clothing", 450, Decimal("24.0"), Decimal("1850.00"), 8200, 25000),
            ("acme official shoes", 320, Decimal("18.5"), Decimal("1420.00"), 5600, 18000),
            ("running sneakers men", 890, Decimal("32.0"), Decimal("2600.00"), 19500, 65000),
            ("trail running shoes waterproof", 410, Decimal("14.0"), Decimal("1250.00"), 9800, 32000),
            ("marathon accessories lightweight", 210, Decimal("6.0"), Decimal("450.00"), 4300, 14000),
            ("unclassified search terms", 110, Decimal("2.0"), Decimal("150.00"), 2200, 5000),
        ]

        rows: list[SearchInsightRow] = []
        for camp in campaigns:
            for cat, clicks, convs, cval, imps, vol in categories:
                rows.append(
                    SearchInsightRow(
                        customer_id=cid,
                        campaign_id=camp.id,
                        campaign_name=camp.name,
                        category_label=cat,
                        date=start_date,
                        clicks=clicks,
                        conversions=convs,
                        conversion_value=cval,
                        impressions=imps,
                        search_volume=vol,
                    )
                )
        return rows

    def query_asset_groups(self, customer_id: str) -> AssetGroupHealthReport:
        cid = customer_id.replace("-", "").strip()
        if cid.startswith("4"):
            return AssetGroupHealthReport()

        ag1 = AssetGroupAuditRow(
            asset_group_id="ag_101",
            asset_group_name="Core Performance Collection",
            campaign_id="10001",
            campaign_name="PMax - Core Product Feed",
            status="ENABLED",
            ad_strength="EXCELLENT",
            headlines_count=12,
            long_headlines_count=4,
            descriptions_count=4,
            images_count=12,
            has_square_image=True,
            has_landscape_image=True,
            has_portrait_image=True,
            videos_count=4,
            has_vertical_video=True,
            search_themes_count=8,
            has_audience_signals=True,
            score=94,
            grade="A+",
            critical_issues=[],
            action_items=["Asset coverage is optimal. Monitor search theme match rate and creative fatigue."],
        )

        ag2 = AssetGroupAuditRow(
            asset_group_id="ag_102",
            asset_group_name="Bestsellers & Promotion",
            campaign_id="10002",
            campaign_name="PMax - High Margin Assets",
            status="ENABLED",
            ad_strength="AVERAGE",
            headlines_count=4,
            long_headlines_count=2,
            descriptions_count=2,
            images_count=6,
            has_square_image=True,
            has_landscape_image=True,
            has_portrait_image=False,
            videos_count=1,
            has_vertical_video=False,
            search_themes_count=2,
            has_audience_signals=True,
            score=66,
            grade="C",
            critical_issues=[
                "Missing 9:16 Vertical Video (Google auto-generates blurry slideshow video on Shorts)",
                "Headlines below best-practice threshold (4/5 minimum)",
            ],
            action_items=[
                "Upload high-resolution 9:16 vertical video immediately to capture premium Shorts CPMs",
                "Add at least 3 distinct value-proposition headlines",
            ],
        )

        ag3 = AssetGroupAuditRow(
            asset_group_id="ag_103",
            asset_group_name="Clearance & Outlet Items",
            campaign_id="10001",
            campaign_name="PMax - Core Product Feed",
            status="ENABLED",
            ad_strength="POOR",
            headlines_count=3,
            long_headlines_count=1,
            descriptions_count=1,
            images_count=2,
            has_square_image=False,
            has_landscape_image=True,
            has_portrait_image=False,
            videos_count=0,
            has_vertical_video=False,
            search_themes_count=0,
            has_audience_signals=False,
            score=38,
            grade="F",
            critical_issues=[
                "Zero video assets uploaded (forfeiting YouTube and Shorts delivery)",
                "Missing audience signals (algorithm exploring broadly without seed targets)",
                "Missing 1:1 square image (limiting Display network formats)",
            ],
            action_items=[
                "Attach Customer Match past-buyer list or Custom In-Market segment",
                "Provide native video creative and 1:1 square assets",
            ],
        )

        groups = [ag1, ag2, ag3]
        avg_score = sum(g.score for g in groups) / len(groups)
        overall_grade = "A" if avg_score >= 90 else "B" if avg_score >= 80 else "C" if avg_score >= 65 else "D" if avg_score >= 50 else "F"

        return AssetGroupHealthReport(
            total_asset_groups=len(groups),
            average_score=round(avg_score, 1),
            overall_grade=overall_grade,
            missing_vertical_video_count=sum(1 for g in groups if not g.has_vertical_video),
            missing_audience_signals_count=sum(1 for g in groups if not g.has_audience_signals),
            asset_groups=groups,
            recommendations=[
                "Upload 9:16 vertical videos to eliminate low-quality auto-generated video on YouTube Shorts.",
                "Enrich Clearance asset group with 1:1 square assets and audience signal seeds to stop algorithm wandering.",
            ],
        )

    def query_product_feed(
        self, customer_id: str, start_date: date, end_date: date
    ) -> ProductFeedAuditReport:
        cid = customer_id.replace("-", "").strip()
        if cid.startswith("4"):
            return ProductFeedAuditReport()

        zombies = [
            ZombieProductRow(
                product_id="SKU-8821",
                title="Pro Carbon Trail Running Poles (120cm)",
                brand="TrailMaster",
                cost=Decimal("420.00"),
                impressions=18400,
                clicks=310,
                conversions=Decimal("0.0"),
                conversion_value=Decimal("0.00"),
                classification="ZOMBIE",
                suggested_action="Exclude SKU or set Custom Label 0 = 'zombie' to immediately halt €420 budget bleed.",
            ),
            ZombieProductRow(
                product_id="SKU-4910",
                title="Gore-Tex Extreme Weather Winter Gaiters",
                brand="AlpineEdge",
                cost=Decimal("340.00"),
                impressions=12200,
                clicks=245,
                conversions=Decimal("0.0"),
                conversion_value=Decimal("0.00"),
                classification="ZOMBIE",
                suggested_action="Check landing page stock availability or lower Target ROAS threshold.",
            ),
            ZombieProductRow(
                product_id="SKU-2104",
                title="Ultralight Carbon Cycling Helmet (Matt Black)",
                brand="AeroVelo",
                cost=Decimal("295.00"),
                impressions=9800,
                clicks=190,
                conversions=Decimal("0.0"),
                conversion_value=Decimal("0.00"),
                classification="ZOMBIE",
                suggested_action="0 conversions in 30 days. Move to separate testing campaign with dedicated budget.",
            ),
            ZombieProductRow(
                product_id="SKU-7731",
                title="Hydration Running Vest 12L Navy",
                brand="TrailMaster",
                cost=Decimal("265.00"),
                impressions=8400,
                clicks=175,
                conversions=Decimal("0.0"),
                conversion_value=Decimal("0.00"),
                classification="ZOMBIE",
                suggested_action="Apply negative product filter in listing group to stop unrewarded spend.",
            ),
        ]

        total_products = 184
        total_cost = Decimal("14250.00")
        zombie_count = 34
        zombie_spend = Decimal("2720.00")
        zombie_share = (zombie_spend / total_cost) * Decimal(100)

        return ProductFeedAuditReport(
            total_products_audited=total_products,
            total_feed_cost=total_cost,
            zombie_products_count=zombie_count,
            zombie_spend=zombie_spend,
            zombie_spend_share=round(zombie_share, 1),
            top_performers_count=28,
            ghost_products_count=122,
            top_zombie_products=zombies,
            estimated_monthly_savings=zombie_spend,
            action_plan=[
                f"Exclude or deprioritize {zombie_count} Zombie SKUs to immediately recover €{zombie_spend:,.2f}/mo (19.1% of feed spend).",
                "Reallocate recovered budget into top 28 converting SKUs currently constrained by target ROAS bids.",
                "Review 122 Ghost SKUs (0 spend) for Merchant Center policy disapprovals or bid under-competitiveness.",
            ],
        )

