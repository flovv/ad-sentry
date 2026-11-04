from __future__ import annotations

import csv
import io
import datetime as dt
from decimal import Decimal
from typing import Any, Iterable
import uuid

from services.data_ingestion.models import BusinessOutcomeDataset, DailyOutcomeRecord


class DataIngestionError(Exception):
    """Raised when uploaded business outcome data violates ingestion constraints."""
    pass


def parse_business_outcomes_csv(
    csv_content: str,
    customer_id: str,
    currency_code: str,
    timezone: str = "UTC",
    attribution_window_days: int = 30,
    conversion_definition: str = "purchase",
) -> BusinessOutcomeDataset:
    """
    Parses and validates CSV input for business outcome metrics.

    Required CSV columns:
    - date (YYYY-MM-DD)
    - total_business_revenue (numeric >= 0)
    - pmax_cost (numeric >= 0)
    - pmax_conversion_value (numeric >= 0)

    Optional columns:
    - organic_revenue
    - non_pmax_spend
    - gross_margin_rate (0.0 to 1.0)
    - promo_active (true/false, 1/0)
    - stock_constrained (true/false, 1/0)
    """
    cleaned_cid = customer_id.replace("-", "").strip()
    if not cleaned_cid.isdigit() or len(cleaned_cid) != 10:
        raise DataIngestionError(f"Customer ID must be 10 digits, got '{customer_id}'")

    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames:
        raise DataIngestionError("CSV file is empty or missing header line.")

    # Normalize header names (lowercase, stripped)
    header_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
    required = ["date", "total_business_revenue", "pmax_cost", "pmax_conversion_value"]
    missing = [col for col in required if col not in header_map]
    if missing:
        raise DataIngestionError(f"Missing required CSV columns: {', '.join(missing)}")

    records: list[DailyOutcomeRecord] = []
    seen_dates: set[dt.date] = set()

    for idx, row in enumerate(reader, start=2):
        try:
            raw_date = row[header_map["date"]].strip()
            record_date = dt.date.fromisoformat(raw_date)
        except Exception:
            raise DataIngestionError(f"Row {idx}: invalid date format '{row.get(header_map['date'])}'. Expected YYYY-MM-DD.")

        if record_date in seen_dates:
            raise DataIngestionError(f"Row {idx}: duplicate date '{record_date}' detected. Dates must be unique.")
        seen_dates.add(record_date)

        def _parse_decimal(col_name: str, required_field: bool = True) -> Decimal | None:
            val = row.get(header_map.get(col_name, ""))
            if val is None or val.strip() == "":
                if required_field:
                    raise DataIngestionError(f"Row {idx}: column '{col_name}' cannot be empty.")
                return None
            try:
                d = Decimal(val.strip().replace("$", "").replace("€", "").replace("£", "").replace(",", ""))
                if d < Decimal(0):
                    raise DataIngestionError(f"Row {idx}: '{col_name}' cannot be negative ({d}).")
                return d
            except Exception as e:
                if isinstance(e, DataIngestionError):
                    raise
                raise DataIngestionError(f"Row {idx}: invalid number '{val}' in column '{col_name}'.")

        def _parse_bool(col_name: str) -> bool:
            val = row.get(header_map.get(col_name, ""))
            if val is None or val.strip() == "":
                return False
            cleaned = val.strip().lower()
            return cleaned in ("true", "1", "yes", "y", "t")

        tot_rev = _parse_decimal("total_business_revenue", required_field=True)
        pm_cost = _parse_decimal("pmax_cost", required_field=True)
        pm_val = _parse_decimal("pmax_conversion_value", required_field=True)
        org_rev = _parse_decimal("organic_revenue", required_field=False)
        non_pm_spend = _parse_decimal("non_pmax_spend", required_field=False)
        margin_rate = _parse_decimal("gross_margin_rate", required_field=False)
        if margin_rate is not None and (margin_rate < Decimal(0) or margin_rate > Decimal(1)):
            raise DataIngestionError(f"Row {idx}: 'gross_margin_rate' must be between 0.0 and 1.0, got {margin_rate}.")

        records.append(
            DailyOutcomeRecord(
                date=record_date,
                total_business_revenue=tot_rev,  # type: ignore
                pmax_cost=pm_cost,  # type: ignore
                pmax_conversion_value=pm_val,  # type: ignore
                organic_revenue=org_rev,
                non_pmax_spend=non_pm_spend,
                gross_margin_rate=margin_rate,
                promo_active=_parse_bool("promo_active"),
                stock_constrained=_parse_bool("stock_constrained"),
            )
        )

    if not records:
        raise DataIngestionError("No valid outcome records found in CSV.")

    # Sort records chronologically
    records.sort(key=lambda r: r.date)

    return BusinessOutcomeDataset(
        dataset_id=f"ds_{uuid.uuid4().hex[:12]}",
        customer_id=cleaned_cid,
        currency_code=currency_code.upper().strip(),
        timezone=timezone,
        attribution_window_days=attribution_window_days,
        conversion_definition=conversion_definition,
        records=records,
        source_type="csv_upload",
    )
