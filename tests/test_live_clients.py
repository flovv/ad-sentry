"""Unit tests for live GoogleAdsApiClient (asset groups & product feed) and MetaGraphApiClient."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
import respx

from pmax_sentry_core.live_client import GoogleAdsApiClient
from pmax_sentry_core.meta_client import MetaGraphApiClient


class _FakeGoogleAdsService:
    """Deterministic fake for GoogleAdsService.search() dispatching by GAQL FROM clause."""

    def __init__(self, responses: dict[str, list[SimpleNamespace]]) -> None:
        self._responses = responses
        self.queries_seen: list[str] = []

    def search(self, customer_id: str, query: str):
        self.queries_seen.append(query)
        for key, rows in self._responses.items():
            if f"FROM {key}" in query:
                return rows
        return []


class _FakeGoogleClient:
    def __init__(self, service: _FakeGoogleAdsService) -> None:
        self._service = service

    def get_service(self, name: str, version: str = "v26"):
        assert name == "GoogleAdsService"
        return self._service


def _enum(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name)


def test_live_client_query_asset_groups():
    ag_rows = [
        SimpleNamespace(
            asset_group=SimpleNamespace(id=101, name="Hero Collection", status=_enum("ENABLED"), ad_strength=_enum("EXCELLENT")),
            campaign=SimpleNamespace(id=1001, name="PMax Main"),
        ),
        SimpleNamespace(
            asset_group=SimpleNamespace(id=102, name="Sparse Group", status=_enum("ENABLED"), ad_strength=_enum("POOR")),
            campaign=SimpleNamespace(id=1001, name="PMax Main"),
        ),
    ]

    asset_rows = [
        # Group 101: rich assets including portrait video
        *[
            SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("HEADLINE")))
            for _ in range(6)
        ],
        *[
            SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("LONG_HEADLINE")))
            for _ in range(2)
        ],
        *[
            SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("DESCRIPTION")))
            for _ in range(4)
        ],
        SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("SQUARE_MARKETING_IMAGE"))),
        SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("MARKETING_IMAGE"))),
        SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("PORTRAIT_MARKETING_IMAGE"))),
        SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("SQUARE_MARKETING_IMAGE"))),
        SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("MARKETING_IMAGE"))),
        SimpleNamespace(asset_group=SimpleNamespace(id=101), asset_group_asset=SimpleNamespace(field_type=_enum("PORTRAIT_VIDEO"))),
        # Group 102: sparse, no video, no square image
        SimpleNamespace(asset_group=SimpleNamespace(id=102), asset_group_asset=SimpleNamespace(field_type=_enum("HEADLINE"))),
        SimpleNamespace(asset_group=SimpleNamespace(id=102), asset_group_asset=SimpleNamespace(field_type=_enum("MARKETING_IMAGE"))),
    ]

    signal_rows = [
        SimpleNamespace(
            asset_group=SimpleNamespace(id=101),
            asset_group_signal=SimpleNamespace(audience=SimpleNamespace(audience="customers/1/audiences/9"), search_theme=SimpleNamespace(text="")),
        ),
        *[
            SimpleNamespace(
                asset_group=SimpleNamespace(id=101),
                asset_group_signal=SimpleNamespace(audience=SimpleNamespace(audience=""), search_theme=SimpleNamespace(text=f"theme {i}")),
            )
            for i in range(4)
        ],
    ]

    svc = _FakeGoogleAdsService({
        "asset_group\n": ag_rows,
        "asset_group_asset": asset_rows,
        "asset_group_signal": signal_rows,
    })
    client = GoogleAdsApiClient(client=_FakeGoogleClient(svc))
    report = client.query_asset_groups("123-456-7890")

    assert report.total_asset_groups == 2
    assert report.missing_vertical_video_count == 1
    assert report.missing_audience_signals_count == 1

    by_id = {g.asset_group_id: g for g in report.asset_groups}
    assert by_id["101"].grade == "A+"
    assert by_id["101"].score == 100
    assert by_id["101"].has_vertical_video is True
    assert by_id["101"].has_audience_signals is True

    assert by_id["102"].grade == "F"
    assert by_id["102"].videos_count == 0
    assert any("Zero video assets" in issue for issue in by_id["102"].critical_issues)


def test_live_client_query_product_feed():
    shopping_rows = [
        # Zombie SKU across 2 days (should aggregate to 150.00 cost, 0 conv)
        SimpleNamespace(
            segments=SimpleNamespace(product_item_id="SKU-Z1", product_title="Winter Boots", product_brand="Alpine"),
            metrics=SimpleNamespace(cost_micros=100_000_000, impressions=4000, clicks=80, conversions=0.0, conversions_value=0.0),
        ),
        SimpleNamespace(
            segments=SimpleNamespace(product_item_id="SKU-Z1", product_title="Winter Boots", product_brand="Alpine"),
            metrics=SimpleNamespace(cost_micros=50_000_000, impressions=2000, clicks=40, conversions=0.0, conversions_value=0.0),
        ),
        # Converting SKU
        SimpleNamespace(
            segments=SimpleNamespace(product_item_id="SKU-WIN", product_title="Trail Shoe", product_brand="Runner"),
            metrics=SimpleNamespace(cost_micros=350_000_000, impressions=12000, clicks=300, conversions=14.0, conversions_value=1800.0),
        ),
        # Ghost SKU (0 spend)
        SimpleNamespace(
            segments=SimpleNamespace(product_item_id="SKU-GHOST", product_title="Socks", product_brand="Runner"),
            metrics=SimpleNamespace(cost_micros=0, impressions=10, clicks=0, conversions=0.0, conversions_value=0.0),
        ),
    ]

    svc = _FakeGoogleAdsService({"shopping_performance_view": shopping_rows})
    client = GoogleAdsApiClient(client=_FakeGoogleClient(svc))
    report = client.query_product_feed("1234567890", dt.date(2026, 10, 1), dt.date(2026, 10, 30))

    assert report.total_products_audited == 3
    assert report.total_feed_cost == Decimal("500.00")
    assert report.zombie_products_count == 1
    assert report.zombie_spend == Decimal("150.00")
    assert report.zombie_spend_share == Decimal("30.0")
    assert report.top_performers_count == 1
    assert report.ghost_products_count == 1
    assert len(report.top_zombie_products) == 1
    assert report.top_zombie_products[0].product_id == "SKU-Z1"
    assert report.top_zombie_products[0].clicks == 120
    assert report.estimated_monthly_savings == Decimal("150.00")


@respx.mock
def test_meta_graph_api_client_live_httpx():
    respx.get("https://graph.facebook.com/v21.0/act_998877").mock(
        return_value=httpx.Response(200, json={"name": "Live Brand Account", "currency": "EUR"})
    )

    respx.get("https://graph.facebook.com/v21.0/act_998877/insights").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "publisher_platform": "instagram",
                        "platform_position": "feed",
                        "spend": "800.00",
                        "impressions": "40000",
                        "clicks": "600",
                        "actions": [
                            {"action_type": "omni_purchase", "value": "30", "7d_click": "20", "1d_click": "15", "1d_view": "10"}
                        ],
                        "action_values": [
                            {"action_type": "omni_purchase", "value": "3000.00", "7d_click": "2000.00", "1d_click": "1500.00", "1d_view": "1000.00"}
                        ],
                    },
                    {
                        "publisher_platform": "audience_network",
                        "platform_position": "rewarded_video",
                        "spend": "200.00",
                        "impressions": "50000",
                        "clicks": "400",
                        "actions": [
                            {"action_type": "omni_purchase", "value": "5", "7d_click": "0", "1d_click": "0", "1d_view": "5"}
                        ],
                        "action_values": [
                            {"action_type": "omni_purchase", "value": "300.00", "7d_click": "0.00", "1d_click": "0.00", "1d_view": "300.00"}
                        ],
                    },
                ],
                "paging": {},
            },
        )
    )

    client = MetaGraphApiClient(access_token="live_test_token_123")
    report = client.build_asc_audit_report(
        account_id="998877",
        start_date=dt.date(2026, 10, 1),
        end_date=dt.date(2026, 10, 31),
        margin=0.40,
    )

    assert report.account_id == "act_998877"
    assert report.account_name == "Live Brand Account"
    assert report.currency_code == "EUR"
    assert report.total_spend == Decimal("1000.00")
    assert report.total_conversion_value == Decimal("3300.00")
    assert report.blended_roas == Decimal("3.30")
    assert report.click_only_roas == Decimal("2.00")
    assert report.audience_network_spend_share == Decimal("0.2000")
    assert report.audience_network_severity == "CRITICAL"
    assert report.attribution_split.ghost_roas_inflation_pct == Decimal("65.0")
    assert report.hurdle is not None
    assert report.net_profit_per_euro_spend == Decimal("-0.20")
    assert len(report.recommendations) >= 2
