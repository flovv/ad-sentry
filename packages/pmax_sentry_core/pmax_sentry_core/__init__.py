"""
pmax-sentry-core: Open-source schemas, API client, normalization, and reconciliation.
"""

from pmax_sentry_core.api import (
    fetch_pmax_delivery,
    fetch_search_insights,
    get_account_info,
    list_pmax_campaigns,
)
from pmax_sentry_core.client import (
    GAQL_CAMPAIGN_TOTALS,
    GAQL_SEARCH_TERM_INSIGHTS,
    GAQL_SEGMENTED_DELIVERY,
    PINNED_API_VERSION,
    BaseGoogleAdsClient,
)
from pmax_sentry_core.exporters import (
    export_delivery_report_csv,
    export_delivery_report_json,
    export_search_insight_csv,
    export_search_insight_json,
)
from pmax_sentry_core.meta_client import (
    BaseMetaAdsClient,
    MetaGraphApiClient,
    MockMetaAdsClient,
    fetch_meta_asc_audit,
)
from pmax_sentry_core.meta_models import (
    MetaAscAuditReport,
    MetaAttributionWindowSplit,
    MetaAudienceCapAudit,
    MetaCreativeFormatRow,
    MetaPlacementRow,
)
from pmax_sentry_core.mock_client import MockGoogleAdsClient
from pmax_sentry_core.models import (
    AccountInfo,
    BrandDiagnosticSummary,
    CampaignInfo,
    CoverageStatus,
    CoverageSummary,
    CrossCampaignOverlapSummary,
    DeliveryReport,
    DeliveryRow,
    EvidenceClass,
    SearchInsightReport,
    SearchInsightRow,
)
from pmax_sentry_core.overlap import calculate_cross_campaign_overlap
from pmax_sentry_core.reconciliation import reconcile_delivery

__all__ = [
    "fetch_pmax_delivery",
    "fetch_search_insights",
    "list_pmax_campaigns",
    "get_account_info",
    "DeliveryRow",
    "CoverageSummary",
    "CrossCampaignOverlapSummary",
    "calculate_cross_campaign_overlap",
    "DeliveryReport",
    "SearchInsightRow",
    "BrandDiagnosticSummary",
    "SearchInsightReport",
    "CampaignInfo",
    "AccountInfo",
    "EvidenceClass",
    "CoverageStatus",
    "reconcile_delivery",
    "export_delivery_report_csv",
    "export_delivery_report_json",
    "export_search_insight_csv",
    "export_search_insight_json",
    "MetaPlacementRow",
    "MetaAttributionWindowSplit",
    "MetaAudienceCapAudit",
    "MetaCreativeFormatRow",
    "MetaAscAuditReport",
    "BaseMetaAdsClient",
    "MockMetaAdsClient",
    "MetaGraphApiClient",
    "fetch_meta_asc_audit",
    "BaseGoogleAdsClient",
    "MockGoogleAdsClient",
    "PINNED_API_VERSION",
    "GAQL_CAMPAIGN_TOTALS",
    "GAQL_SEGMENTED_DELIVERY",
    "GAQL_SEARCH_TERM_INSIGHTS",
]
