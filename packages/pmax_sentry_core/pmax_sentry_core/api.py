from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from pmax_sentry_core.client import BaseGoogleAdsClient
from pmax_sentry_core.mock_client import MockGoogleAdsClient
from pmax_sentry_core.models import (
    AccountInfo,
    CampaignInfo,
    DeliveryReport,
    SearchInsightReport,
)


def _get_client(
    config_path: Path | str | None = None,
    client: BaseGoogleAdsClient | None = None,
) -> BaseGoogleAdsClient:
    if client is not None:
        return client

    if config_path is not None:
        p = Path(config_path)
        if p.exists():
            from pmax_sentry_core.live_client import GoogleAdsApiClient
            return GoogleAdsApiClient(config_path=p)

    # Check standard google-ads.yaml in current dir or home dir
    default_cfg = Path("google-ads.yaml")
    home_cfg = Path.home() / "google-ads.yaml"
    if default_cfg.exists():
        from pmax_sentry_core.live_client import GoogleAdsApiClient
        return GoogleAdsApiClient(config_path=default_cfg)
    elif home_cfg.exists():
        from pmax_sentry_core.live_client import GoogleAdsApiClient
        return GoogleAdsApiClient(config_path=home_cfg)

    # Return Mock client for offline / demo execution without credentials
    return MockGoogleAdsClient()


def fetch_pmax_delivery(
    customer_id: str,
    start_date: date,
    end_date: date,
    config_path: Path | str | None = None,
    client: BaseGoogleAdsClient | None = None,
) -> DeliveryReport:
    """
    Public Python API to fetch and reconcile PMax delivery report for a customer account.
    """
    c = _get_client(config_path=config_path, client=client)
    return c.build_delivery_report(customer_id=customer_id, start_date=start_date, end_date=end_date)


def fetch_search_insights(
    customer_id: str,
    start_date: date,
    end_date: date,
    config_path: Path | str | None = None,
    brand_dictionary: list[str] | None = None,
    client: BaseGoogleAdsClient | None = None,
) -> SearchInsightReport:
    """
    Public Python API to fetch search-term category insights for PMax campaigns.
    """
    c = _get_client(config_path=config_path, client=client)
    return c.build_search_insight_report(
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        brand_dictionary=brand_dictionary,
    )


def list_pmax_campaigns(
    customer_id: str,
    config_path: Path | str | None = None,
    client: BaseGoogleAdsClient | None = None,
) -> list[CampaignInfo]:
    """
    Public Python API to list all PMax campaigns in the account.
    """
    c = _get_client(config_path=config_path, client=client)
    return c.list_pmax_campaigns(customer_id)


def get_account_info(
    customer_id: str,
    config_path: Path | str | None = None,
    client: BaseGoogleAdsClient | None = None,
) -> AccountInfo:
    """
    Public Python API to get account metadata (currency, timezone, descriptive name).
    """
    c = _get_client(config_path=config_path, client=client)
    return c.get_account_info(customer_id)
