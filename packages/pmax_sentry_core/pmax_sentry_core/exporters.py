from __future__ import annotations

import csv
import io
import json
from decimal import Decimal
from typing import Any

from pmax_sentry_core.models import DeliveryReport, SearchInsightReport


def export_delivery_report_json(report: DeliveryReport, indent: int = 2) -> str:
    """Exports delivery report to JSON string matching schema."""
    return report.model_dump_json(indent=indent)


def export_delivery_report_csv(report: DeliveryReport) -> str:
    """
    Exports delivery report to clean CSV string.
    Includes metadata headers detailing customer, dates, currency, API version, and coverage.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Metadata comments
    writer.writerow([f"# PMax Delivery Mix Report"])
    writer.writerow([f"# Customer ID: {report.customer_id}"])
    writer.writerow([f"# Reporting Window: {report.start_date} to {report.end_date}"])
    writer.writerow([f"# Account Currency: {report.currency_code} | Timezone: {report.timezone}"])
    writer.writerow([f"# API Version: {report.api_version} | Generated: {report.generated_at.isoformat()}"])
    writer.writerow(
        [
            f"# Coverage Status: {report.coverage.status} | "
            f"Segmented Cost: {report.coverage.segmented_cost_micros} micros | "
            f"Total Cost: {report.coverage.unsegmented_cost_micros} micros | "
            f"Difference: {report.coverage.difference_micros} micros | "
            f"Coverage Ratio: {report.coverage.coverage_ratio if report.coverage.coverage_ratio is not None else 'N/A'}"
        ]
    )
    for reason in report.coverage.reasons:
        writer.writerow([f"# Coverage Note: {reason}"])
    for warning in report.warnings:
        writer.writerow([f"# Warning: {warning}"])

    # Header
    writer.writerow(
        [
            "customer_id",
            "campaign_id",
            "campaign_name",
            "date",
            "channel",
            "uses_product_data",
            "uses_video",
            "currency_code",
            "cost_micros",
            "cost",
            "impressions",
            "clicks",
            "conversions",
            "conversion_value",
            "reported_roas",
        ]
    )

    for row in report.rows:
        writer.writerow(
            [
                row.customer_id,
                row.campaign_id,
                row.campaign_name,
                row.date.isoformat(),
                row.channel,
                "" if row.uses_product_data is None else str(row.uses_product_data),
                "" if row.uses_video is None else str(row.uses_video),
                row.currency_code,
                row.cost_micros,
                f"{row.cost:.2f}",
                row.impressions,
                row.clicks,
                f"{row.conversions:.2f}",
                f"{row.conversion_value:.2f}",
                f"{row.roas:.2f}" if row.roas is not None else "0.00",
            ]
        )

    return output.getvalue()


def export_search_insight_json(report: SearchInsightReport, indent: int = 2) -> str:
    """Exports search insights report to JSON string matching schema."""
    return report.model_dump_json(indent=indent)


def export_search_insight_csv(report: SearchInsightReport) -> str:
    """
    Exports search insights to clean CSV string.
    Clearly notes that search insights are demand metrics without spend.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([f"# PMax Search Demand Insights Report"])
    writer.writerow([f"# Customer ID: {report.customer_id}"])
    writer.writerow([f"# Date Range: {report.start_date} to {report.end_date}"])
    writer.writerow([f"# API Version: {report.api_version}"])
    writer.writerow([f"# NOTICE: Search insight metrics represent search demand and do NOT contain cost."])
    for w in report.warnings:
        writer.writerow([f"# Warning: {w}"])

    if report.brand_diagnostic:
        diag = report.brand_diagnostic
        writer.writerow([f"# Brand Classifier Version: {diag.classifier_version}"])
        writer.writerow([f"# Brand Dictionary: {', '.join(diag.brand_dictionary)}"])
        writer.writerow(
            [
                f"# Query Shares: Classifiable={diag.classifiable_query_share:.1%}, "
                f"Brand={diag.brand_query_share:.1%}, "
                f"Generic={diag.generic_query_share:.1%}, "
                f"Unknown={diag.unknown_query_share:.1%}"
            ]
        )

    writer.writerow(
        [
            "customer_id",
            "campaign_id",
            "campaign_name",
            "category_label",
            "date",
            "clicks",
            "conversions",
            "conversion_value",
            "impressions",
            "search_volume",
        ]
    )

    for row in report.rows:
        writer.writerow(
            [
                row.customer_id,
                row.campaign_id,
                row.campaign_name,
                row.category_label,
                row.date.isoformat() if row.date else "",
                row.clicks,
                f"{row.conversions:.2f}",
                f"{row.conversion_value:.2f}",
                row.impressions,
                row.search_volume if row.search_volume is not None else "",
            ]
        )

    return output.getvalue()
