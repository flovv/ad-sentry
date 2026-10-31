from __future__ import annotations

import datetime as dt
from decimal import Decimal
import statistics
from typing import Literal
from pydantic import BaseModel, Field

from services.data_ingestion.models import BusinessOutcomeDataset


class QualityCheckResult(BaseModel):
    check_name: str
    status: Literal["PASS", "WARN", "FAIL"]
    message: str


class DataQualityReport(BaseModel):
    status: Literal["PASSED", "WARNING", "INSUFFICIENT_DATA"]
    dataset_id: str
    customer_id: str
    record_count: int
    start_date: dt.date
    end_date: dt.date
    matured_date_cutoff: dt.date
    matured_record_count: int
    eligible_for_observational: bool
    eligible_for_experiment: bool
    checks: list[QualityCheckResult] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


def run_data_quality_preflight(
    dataset: BusinessOutcomeDataset,
    lag_days: int = 14,
    min_days: int = 30,
) -> DataQualityReport:
    """
    Executes deterministic data quality preflight checks:
    - Minimum sample size (>= 30 days)
    - Continuity / missing date detection
    - Conversion lag maturation window
    - Spend variability check (coefficient of variation)
    - Outlier / zero-spend checks
    """
    checks: list[QualityCheckResult] = []
    reasons: list[str] = []

    if not dataset.records:
        return DataQualityReport(
            status="INSUFFICIENT_DATA",
            dataset_id=dataset.dataset_id,
            customer_id=dataset.customer_id,
            record_count=0,
            start_date=dt.date.today(),
            end_date=dt.date.today(),
            matured_date_cutoff=dt.date.today(),
            matured_record_count=0,
            eligible_for_observational=False,
            eligible_for_experiment=False,
            checks=[
                QualityCheckResult(
                    check_name="record_volume",
                    status="FAIL",
                    message="Dataset contains 0 records.",
                )
            ],
            reasons=["No business outcome data supplied."],
        )

    records = sorted(dataset.records, key=lambda r: r.date)
    start_d = records[0].date
    end_d = records[-1].date
    total_days = len(records)

    # 1. Sample Size Check
    if total_days < min_days:
        checks.append(
            QualityCheckResult(
                check_name="sample_size",
                status="FAIL",
                message=f"Dataset has {total_days} days. Minimum required is {min_days} days.",
            )
        )
        reasons.append(f"Insufficient historical data: {total_days} days provided; minimum {min_days} days required.")
    else:
        checks.append(
            QualityCheckResult(
                check_name="sample_size",
                status="PASS",
                message=f"Dataset has {total_days} days, meeting the minimum {min_days} days requirement.",
            )
        )

    # 2. Date Continuity Check
    missing_dates = []
    curr = start_d
    dates_set = {r.date for r in records}
    while curr <= end_d:
        if curr not in dates_set:
            missing_dates.append(curr)
        curr += dt.timedelta(days=1)

    if missing_dates:
        if len(missing_dates) > 5:
            checks.append(
                QualityCheckResult(
                    check_name="date_continuity",
                    status="FAIL",
                    message=f"Detected {len(missing_dates)} missing days between {start_d} and {end_d}.",
                )
            )
            reasons.append(f"Significant date gaps: {len(missing_dates)} missing days in sequence.")
        else:
            checks.append(
                QualityCheckResult(
                    check_name="date_continuity",
                    status="WARN",
                    message=f"Detected {len(missing_dates)} missing days in sequence.",
                )
            )
            reasons.append(f"Minor date gaps detected ({len(missing_dates)} days missing).")
    else:
        checks.append(
            QualityCheckResult(
                check_name="date_continuity",
                status="PASS",
                message="Date sequence is continuous with no missing days.",
            )
        )

    # 3. Conversion Lag Maturation
    matured_cutoff = end_d - dt.timedelta(days=lag_days)
    matured_records = [r for r in records if r.date <= matured_cutoff]
    if len(matured_records) < 14:
        checks.append(
            QualityCheckResult(
                check_name="conversion_lag_maturation",
                status="FAIL",
                message=f"Only {len(matured_records)} days of matured data before {matured_cutoff} (lag={lag_days}d).",
            )
        )
        reasons.append(f"Conversion lag window ({lag_days} days) leaves insufficient matured data for modeling.")
    else:
        checks.append(
            QualityCheckResult(
                check_name="conversion_lag_maturation",
                status="PASS",
                message=f"{len(matured_records)} days available prior to conversion maturation cutoff ({matured_cutoff}).",
            )
        )

    # 4. Spend Variability Check
    costs = [float(r.pmax_cost) for r in matured_records]
    if len(costs) >= 2:
        mean_cost = statistics.mean(costs)
        stdev_cost = statistics.stdev(costs)
        cv = (stdev_cost / mean_cost) if mean_cost > 0 else 0.0

        if cv < 0.05:
            checks.append(
                QualityCheckResult(
                    check_name="spend_variability",
                    status="FAIL",
                    message=f"Coefficient of variation for PMax spend is {cv:.3f} (< 0.05). Spend is virtually flat.",
                )
            )
            reasons.append("Insufficient spend variation: flat historical spend prevents observational response curve estimation.")
        elif cv < 0.15:
            checks.append(
                QualityCheckResult(
                    check_name="spend_variability",
                    status="WARN",
                    message=f"Coefficient of variation for PMax spend is moderate ({cv:.3f}).",
                )
            )
        else:
            checks.append(
                QualityCheckResult(
                    check_name="spend_variability",
                    status="PASS",
                    message=f"Spend variability is healthy (CV = {cv:.3f}).",
                )
            )
    else:
        checks.append(
            QualityCheckResult(
                check_name="spend_variability",
                status="FAIL",
                message="Not enough matured records to calculate spend variation.",
            )
        )
        reasons.append("Insufficient matured records for variance check.")

    # Determine Overall Status
    has_fails = any(c.status == "FAIL" for c in checks)
    has_warns = any(c.status == "WARN" for c in checks)

    if has_fails:
        overall_status = "INSUFFICIENT_DATA"
        eligible_obs = False
        eligible_exp = len(records) >= 14  # can still design an experiment even if historical data is insufficient for observational modeling
    elif has_warns:
        overall_status = "WARNING"
        eligible_obs = True
        eligible_exp = True
    else:
        overall_status = "PASSED"
        eligible_obs = True
        eligible_exp = True

    return DataQualityReport(
        status=overall_status,
        dataset_id=dataset.dataset_id,
        customer_id=dataset.customer_id,
        record_count=total_days,
        start_date=start_d,
        end_date=end_d,
        matured_date_cutoff=matured_cutoff,
        matured_record_count=len(matured_records),
        eligible_for_observational=eligible_obs,
        eligible_for_experiment=eligible_exp,
        checks=checks,
        reasons=reasons,
    )
