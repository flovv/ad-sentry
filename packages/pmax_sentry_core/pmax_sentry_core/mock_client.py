from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import random

from pmax_sentry_core.client import BaseGoogleAdsClient
from pmax_sentry_core.models import (
    AccountInfo,
    CampaignInfo,
    DeliveryRow,
    SearchInsightRow,
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
