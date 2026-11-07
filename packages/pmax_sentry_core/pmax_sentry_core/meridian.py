"""
Google Meridian & Bayesian Media Mix Modeling (MMM) Bridge for PMax Sentry.

Solves the primary econometric headache of automated Google campaigns:
Performance Max blends Search, Shopping, YouTube, Display, and Discover into
a single opaque spend figure, violating the econometric assumption of orthogonal
channel inputs.

This module deconstructs PMax delivery reports into orthogonal channel execution
and financial time-series aligned with Google Meridian, PyMC-Marketing, and Meta Robyn.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from pmax_sentry_core.models import DeliveryReport, DeliveryRow

# Standard orthogonal channels deconstructed from PMax
CANONICAL_PMAX_MERIDIAN_CHANNELS = [
    "pmax_shopping",
    "pmax_search",
    "pmax_youtube",
    "pmax_display",
    "pmax_discovery",
]


def classify_pmax_channel_for_mmm(
    row: DeliveryRow,
    collapse_discovery_to_display: bool = False,
) -> str:
    """Classifies a PMax DeliveryRow into an orthogonal Media Mix Modeling (MMM) channel.

    Rules:
      1. Google Search + uses_product_data=True  -> 'pmax_shopping'
      2. Google Search (Text) / Search Partners  -> 'pmax_search'
      3. YouTube (In-stream, Shorts) / uses_video -> 'pmax_youtube'
      4. Display Network (Remarketing / Web)     -> 'pmax_display'
      5. Discover / Gmail                        -> 'pmax_discovery' (or 'pmax_display')
    """
    ch = row.channel.lower()

    if "search" in ch:
        if row.uses_product_data is True:
            return "pmax_shopping"
        return "pmax_search"
    elif "youtube" in ch or row.uses_video is True:
        return "pmax_youtube"
    elif "display" in ch:
        return "pmax_display"
    elif any(k in ch for k in ["discover", "gmail"]):
        if collapse_discovery_to_display:
            return "pmax_display"
        return "pmax_discovery"
    else:
        if collapse_discovery_to_display:
            return "pmax_display"
        return "pmax_discovery"


def _to_period_start_date(date_val: Any, freq: str) -> str:
    """Aligns a date to the start of the MMM period (e.g. Monday for weekly MMM)."""
    import pandas as pd

    ts = pd.to_datetime(date_val)
    f_upper = freq.upper()

    if f_upper in ("W-MON", "WEEKLY", "W"):
        # In pandas, dt.to_period("W-SUN") aligns Monday through Sunday with week ending Sunday.
        # start_time gives the Monday week start date.
        period = ts.to_period("W-SUN")
        return period.start_time.strftime("%Y-%m-%d")
    elif f_upper in ("D", "DAILY"):
        return ts.strftime("%Y-%m-%d")
    elif f_upper in ("M", "MONTHLY"):
        period = ts.to_period("M")
        return period.start_time.strftime("%Y-%m-%d")
    else:
        # Default fallback: period start via pandas to_period
        try:
            period = ts.to_period(freq)
            return period.start_time.strftime("%Y-%m-%d")
        except Exception:
            return ts.strftime("%Y-%m-%d")


def export_meridian_pmax(
    report: DeliveryReport,
    *,
    freq: str = "W-MON",
    geo: str = "national",
    collapse_discovery_to_display: bool = False,
    include_clicks: bool = True,
) -> Any:
    """Exports a DeliveryReport into a Pandas DataFrame formatted for Google Meridian.

    Produces period-aligned rows with orthogonal media execution metrics
    (impressions) and financial metrics (spend) for each deconstructed PMax channel.

    Args:
        report: DeliveryReport instance from fetch_pmax_delivery.
        freq: Frequency offset alias matching MMM time-grain (default: 'W-MON' for weekly Monday start).
        geo: Geographic grain (default: 'national').
        collapse_discovery_to_display: When True, merges Discover and Gmail into pmax_display.
        include_clicks: Whether to include '<channel>_clicks' columns alongside impressions.

    Returns:
        pandas.DataFrame formatted with columns:
          ['date', 'geo', 'conversions', 'conversion_value',
           '<channel>_spend', '<channel>_impressions', ('<channel>_clicks')...]
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for export_meridian_pmax. Install with `pip install pandas` or `pip install ad-sentry[all]`."
        )

    if not report.rows:
        cols = ["date", "geo", "conversions", "conversion_value"]
        channels = [
            ch
            for ch in CANONICAL_PMAX_MERIDIAN_CHANNELS
            if not (collapse_discovery_to_display and ch == "pmax_discovery")
        ]
        for ch in channels:
            cols.extend([f"{ch}_spend", f"{ch}_impressions"])
            if include_clicks:
                cols.append(f"{ch}_clicks")
        return pd.DataFrame(columns=cols)

    # 1. Transform rows into unaggregated records with period alignment
    records = []
    channels_seen = set()

    for r in report.rows:
        period_str = _to_period_start_date(r.date, freq)
        mmm_channel = classify_pmax_channel_for_mmm(
            r, collapse_discovery_to_display=collapse_discovery_to_display
        )
        channels_seen.add(mmm_channel)

        records.append(
            {
                "date": period_str,
                "geo": geo,
                "channel": mmm_channel,
                "cost": float(r.cost),
                "impressions": int(r.impressions),
                "clicks": int(r.clicks),
                "conversions": float(r.conversions),
                "conversion_value": float(r.conversion_value),
            }
        )

    raw_df = pd.DataFrame(records)

    # 2. Canonical list of channels (preserve canonical order)
    active_channels = [
        ch for ch in CANONICAL_PMAX_MERIDIAN_CHANNELS if ch in channels_seen
    ]
    # Add any custom unexpected channels
    for ch in sorted(channels_seen):
        if ch not in active_channels:
            active_channels.append(ch)

    # 3. Aggregate period totals (KPI totals)
    period_kpis = (
        raw_df.groupby(["date", "geo"])[["conversions", "conversion_value"]]
        .sum()
        .reset_index()
    )

    # 4. Pivot spend, impressions, and clicks per channel
    pivot_spend = raw_df.pivot_table(
        index=["date", "geo"],
        columns="channel",
        values="cost",
        aggfunc="sum",
        fill_value=0.0,
    )
    pivot_spend.columns = [f"{col}_spend" for col in pivot_spend.columns]

    pivot_impr = raw_df.pivot_table(
        index=["date", "geo"],
        columns="channel",
        values="impressions",
        aggfunc="sum",
        fill_value=0,
    )
    pivot_impr.columns = [f"{col}_impressions" for col in pivot_impr.columns]

    if include_clicks:
        pivot_clicks = raw_df.pivot_table(
            index=["date", "geo"],
            columns="channel",
            values="clicks",
            aggfunc="sum",
            fill_value=0,
        )
        pivot_clicks.columns = [f"{col}_clicks" for col in pivot_clicks.columns]
    else:
        pivot_clicks = None

    # 5. Join components into final Meridian DataFrame
    merged = period_kpis.merge(pivot_spend, on=["date", "geo"], how="left")
    merged = merged.merge(pivot_impr, on=["date", "geo"], how="left")
    if pivot_clicks is not None:
        merged = merged.merge(pivot_clicks, on=["date", "geo"], how="left")

    # Fill any remaining NaNs with 0
    merged = merged.fillna(0.0)

    # Sort by date chronologically
    merged = merged.sort_values(by=["date", "geo"]).reset_index(drop=True)

    # Arrange columns in clean, deterministic order
    ordered_cols = ["date", "geo", "conversions", "conversion_value"]
    for ch in active_channels:
        spend_col = f"{ch}_spend"
        impr_col = f"{ch}_impressions"
        if spend_col in merged.columns:
            ordered_cols.append(spend_col)
        if impr_col in merged.columns:
            ordered_cols.append(impr_col)
        if include_clicks:
            click_col = f"{ch}_clicks"
            if click_col in merged.columns:
                ordered_cols.append(click_col)

    # Round spend and values for clean modeling
    for col in merged.columns:
        if col.endswith("_spend") or col in ("conversion_value", "conversions"):
            merged[col] = merged[col].round(2)

    return merged[ordered_cols]


def generate_meridian_spec(
    channels: Sequence[str] | None = None,
    kpi_col: str = "conversions",
) -> dict[str, Any]:
    """Generates the dictionary specification required by Google Meridian's InputData builder."""
    if channels is None:
        chs = list(CANONICAL_PMAX_MERIDIAN_CHANNELS)
    else:
        chs = list(channels)

    media_cols = [f"{ch}_impressions" for ch in chs]
    media_spend_cols = [f"{ch}_spend" for ch in chs]

    return {
        "time_col": "date",
        "geo_col": "geo",
        "kpi_col": kpi_col,
        "media_channels": chs,
        "media_cols": media_cols,
        "media_spend_cols": media_spend_cols,
    }


def generate_meridian_python_snippet(
    channels: Sequence[str] | None = None,
    kpi_col: str = "conversions",
    csv_filename: str = "meridian_pmax_input.csv",
) -> str:
    """Generates clean, copy-pasteable Python code to initialize Google Meridian with the deconstructed dataset."""
    spec = generate_meridian_spec(channels=channels, kpi_col=kpi_col)
    chs = spec["media_channels"]

    code = f'''# Google Meridian Ingestion Script for Deconstructed PMax Data
# Generated by Ad Sentry (pmax-sentry)

import pandas as pd
from meridian.data.data_frame_input_data_builder import DataFrameInputDataBuilder

# 1. Load deconstructed PMax weekly dataset
df = pd.read_csv("{csv_filename}")
df["date"] = pd.to_datetime(df["date"])

# 2. Configure Meridian InputData builder with deconstructed orthogonal channels
channels = {chs!r}

builder = (
    DataFrameInputDataBuilder(
        data=df,
        time_col="date",
        geo_col="geo",
    )
    .with_kpi(kpi_col="{kpi_col}")
    .with_media(
        media_cols=[f"{{ch}}_impressions" for ch in channels],
        media_spend_cols=[f"{{ch}}_spend" for ch in channels],
        media_channels=channels,
    )
)

# 3. Build input data container ready for Meridian model estimation
input_data = builder.build()
print(f"Meridian input loaded successfully: {{len(df)}} periods across {{len(channels)}} channels.")
'''
    return code


def export_meridian_csv(
    report: DeliveryReport,
    *,
    freq: str = "W-MON",
    geo: str = "national",
    collapse_discovery_to_display: bool = False,
    include_clicks: bool = True,
) -> str:
    """Exports a DeliveryReport to a Meridian-compatible CSV string with metadata headers."""
    df = export_meridian_pmax(
        report,
        freq=freq,
        geo=geo,
        collapse_discovery_to_display=collapse_discovery_to_display,
        include_clicks=include_clicks,
    )

    out = io.StringIO()
    # Metadata header
    out.write("# Ad Sentry PMax Deconstructed Dataset for Google Meridian MMM\n")
    out.write(f"# Customer ID: {report.customer_id}\n")
    out.write(f"# Reporting Window: {report.start_date} to {report.end_date}\n")
    out.write(f"# Account Currency: {report.currency_code} | Frequency: {freq} | Geo: {geo}\n")
    out.write(f"# Generated At: {report.generated_at.isoformat()} | API Version: {report.api_version}\n")
    out.write("# Channels: Shopping, Search, YouTube Video, Display Network, Discovery/Gmail\n")

    # CSV data
    df.to_csv(out, index=False)
    return out.getvalue()
