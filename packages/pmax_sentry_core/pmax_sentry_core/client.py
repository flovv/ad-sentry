from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Sequence

from pmax_sentry_core.models import (
    AccountInfo,
    BrandDiagnosticSummary,
    CampaignInfo,
    CoverageSummary,
    CrossCampaignOverlapSummary,
    DeliveryReport,
    DeliveryRow,
    SearchInsightReport,
    SearchInsightRow,
)
from pmax_sentry_core.overlap import calculate_cross_campaign_overlap
from pmax_sentry_core.reconciliation import reconcile_delivery

logger = logging.getLogger("pmax_sentry.client")

PINNED_API_VERSION = "v26"

GAQL_CAMPAIGN_TOTALS = """
SELECT
  campaign.id,
  campaign.name,
  campaign.advertising_channel_type,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM campaign
WHERE campaign.advertising_channel_type {channel_types_condition}
  AND segments.date BETWEEN '{start_date}' AND '{end_date}'
"""

GAQL_SEGMENTED_DELIVERY = """
SELECT
  campaign.id,
  campaign.name,
  campaign.advertising_channel_type,
  segments.date,
  segments.ad_network_type,
  segments.ad_using_product_data,
  segments.ad_using_video,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value,
  metrics.view_through_conversions
FROM campaign
WHERE campaign.advertising_channel_type {channel_types_condition}
  AND segments.date BETWEEN '{start_date}' AND '{end_date}'
"""

GAQL_SEARCH_TERM_INSIGHTS = """
SELECT
  campaign.id,
  campaign.name,
  campaign_search_term_insight.category_label,
  segments.date,
  metrics.clicks,
  metrics.conversions,
  metrics.conversions_value,
  metrics.impressions,
  metrics.search_volume
FROM campaign_search_term_insight
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
  AND segments.date BETWEEN '{start_date}' AND '{end_date}'
"""


class BaseGoogleAdsClient(ABC):
    """Abstract Google Ads client interface pinned to v26."""

    api_version: str = PINNED_API_VERSION

    @abstractmethod
    def get_account_info(self, customer_id: str) -> AccountInfo:
        """Fetch customer account details (currency, timezone, descriptive name)."""
        pass

    @abstractmethod
    def list_pmax_campaigns(
        self, customer_id: str, include_demand_gen: bool = False
    ) -> list[CampaignInfo]:
        """Fetch all eligible PMax (and optionally Demand Gen) campaigns in customer account."""
        pass

    @abstractmethod
    def query_unsegmented_totals(
        self, customer_id: str, start_date: date, end_date: date, include_demand_gen: bool = False
    ) -> int:
        """Fetch unsegmented total cost_micros across all PMax (and optionally Demand Gen) campaigns for date range."""
        pass

    @abstractmethod
    def query_segmented_delivery(
        self, customer_id: str, start_date: date, end_date: date, include_demand_gen: bool = False
    ) -> list[DeliveryRow]:
        """Fetch segmented PMax (and optionally Demand Gen) delivery records by channel and format flags."""
        pass

    @abstractmethod
    def query_search_insights(
        self, customer_id: str, start_date: date, end_date: date
    ) -> list[SearchInsightRow]:
        """Fetch search-term category insights. NEVER requests cost metrics."""
        pass

    def build_delivery_report(
        self,
        customer_id: str,
        start_date: date,
        end_date: date,
        include_demand_gen: bool = False,
    ) -> DeliveryReport:
        account = self.get_account_info(customer_id)
        segmented_rows = self.query_segmented_delivery(
            customer_id, start_date, end_date, include_demand_gen=include_demand_gen
        )
        unsegmented_cost_micros = self.query_unsegmented_totals(
            customer_id, start_date, end_date, include_demand_gen=include_demand_gen
        )

        coverage = reconcile_delivery(segmented_rows, unsegmented_cost_micros)
        warnings: list[str] = []

        if coverage.status == "PARTIAL":
            warnings.append(
                f"Delivery report has PARTIAL coverage: segmented cost differs from campaign totals by {coverage.difference_micros} micros."
            )
        elif coverage.status == "UNAVAILABLE":
            warnings.append("Segmented delivery data is UNAVAILABLE for this customer/date range.")

        overlap = calculate_cross_campaign_overlap(segmented_rows) if include_demand_gen else None
        included_types = ["PERFORMANCE_MAX", "DEMAND_GEN"] if include_demand_gen else ["PERFORMANCE_MAX"]

        return DeliveryReport(
            schema_version="1.0.0",
            api_version=self.api_version,
            generated_at=datetime.now(timezone.utc),
            customer_id=customer_id,
            currency_code=account.currency_code,
            timezone=account.time_zone,
            start_date=start_date,
            end_date=end_date,
            rows=segmented_rows,
            coverage=coverage,
            warnings=warnings,
            included_channel_types=included_types,
            cross_campaign_overlap=overlap,
        )

    def build_search_insight_report(
        self,
        customer_id: str,
        start_date: date,
        end_date: date,
        brand_dictionary: list[str] | None = None,
    ) -> SearchInsightReport:
        rows = self.query_search_insights(customer_id, start_date, end_date)
        brand_diagnostic: BrandDiagnosticSummary | None = None

        if brand_dictionary is not None and len(rows) > 0:
            brand_words = {b.strip().lower() for b in brand_dictionary if b.strip()}
            total_clicks = sum(r.clicks for r in rows) or len(rows)
            brand_clicks = 0
            generic_clicks = 0
            unknown_clicks = 0

            for r in rows:
                cat_lower = r.category_label.lower()
                weight = r.clicks or 1
                if any(bw in cat_lower for bw in brand_words):
                    brand_clicks += weight
                elif "unknown" in cat_lower or "unclassified" in cat_lower or not cat_lower.strip():
                    unknown_clicks += weight
                else:
                    generic_clicks += weight

            total_weight = brand_clicks + generic_clicks + unknown_clicks
            if total_weight > 0:
                classifiable_share = Decimal(brand_clicks + generic_clicks) / Decimal(total_weight)
                brand_share = Decimal(brand_clicks) / Decimal(total_weight)
                generic_share = Decimal(generic_clicks) / Decimal(total_weight)
                unknown_share = Decimal(unknown_clicks) / Decimal(total_weight)
            else:
                classifiable_share = Decimal("0")
                brand_share = Decimal("0")
                generic_share = Decimal("0")
                unknown_share = Decimal("1.0")

            brand_diagnostic = BrandDiagnosticSummary(
                classifier_version="1.0.0",
                brand_dictionary=brand_dictionary,
                classifiable_query_share=classifiable_share.quantize(Decimal("0.0001")),
                brand_query_share=brand_share.quantize(Decimal("0.0001")),
                generic_query_share=generic_share.quantize(Decimal("0.0001")),
                unknown_query_share=unknown_share.quantize(Decimal("0.0001")),
                notes=[
                    "Classification computed against visible search-term category labels only.",
                    "Search categories do not include spend; query shares reflect click/volume weights, not ad cost.",
                ],
            )

        return SearchInsightReport(
            schema_version="1.0.0",
            api_version=self.api_version,
            generated_at=datetime.now(timezone.utc),
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            rows=rows,
            brand_diagnostic=brand_diagnostic,
        )
