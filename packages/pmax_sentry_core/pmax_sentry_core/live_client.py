from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from pmax_sentry_core.client import (
    GAQL_CAMPAIGN_TOTALS,
    GAQL_SEARCH_TERM_INSIGHTS,
    GAQL_SEGMENTED_DELIVERY,
    BaseGoogleAdsClient,
)
from pmax_sentry_core.models import (
    AccountInfo,
    CampaignInfo,
    DeliveryRow,
    SearchInsightRow,
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
