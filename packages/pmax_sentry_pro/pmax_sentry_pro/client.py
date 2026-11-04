from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, Literal, Optional
import httpx
from pydantic import BaseModel

from pmax_sentry_core.models import DeliveryReport, SearchInsightReport
from services.data_ingestion.models import BusinessOutcomeDataset
from services.data_quality.preflight import DataQualityReport
from services.decision_contracts.models import DecisionContract
from services.incrementality.models import (
    EconomicHurdleResult,
    ExperimentPlan,
    ExperimentPowerAnalysis,
    ExperimentResultAnalysis,
    ObservationalDiagnosticResult,
)


class PMaxSentryProClient:
    """
    Thin client for PMax Sentry Pro API service.
    Can talk to a remote hosted service (via base_url) or in-process ASGI app.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        workspace_id: str = "default_ws",
        api_key: Optional[str] = None,
        app: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workspace_id = workspace_id
        self.api_key = api_key

        headers = {
            "x-workspace-id": self.workspace_id,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if app is not None:
            from starlette.testclient import TestClient
            self._http = TestClient(app=app, base_url=self.base_url, headers=headers)
        else:
            self._http = httpx.Client(base_url=self.base_url, headers=headers, timeout=30.0)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> PMaxSentryProClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        resp = self._http.get("/health")
        resp.raise_for_status()
        return resp.json()

    def get_workspace(self) -> dict[str, Any]:
        resp = self._http.get("/workspaces/current")
        resp.raise_for_status()
        return resp.json()

    def connect_account(self, customer_id: str) -> dict[str, Any]:
        resp = self._http.post("/workspaces/accounts/connect", json={"customer_id": customer_id})
        resp.raise_for_status()
        return resp.json()

    def disconnect_account(self, customer_id: str) -> dict[str, Any]:
        resp = self._http.delete(f"/workspaces/accounts/{customer_id}")
        resp.raise_for_status()
        return resp.json()

    def delete_workspace_data(self) -> dict[str, Any]:
        resp = self._http.delete("/workspaces/current")
        resp.raise_for_status()
        return resp.json()

    def get_delivery_report(
        self, customer_id: str, start_date: dt.date, end_date: dt.date
    ) -> DeliveryReport:
        payload = {
            "customer_id": customer_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        resp = self._http.post("/reports/delivery", json=payload)
        resp.raise_for_status()
        return DeliveryReport.model_validate(resp.json())

    def get_search_insights(
        self,
        customer_id: str,
        start_date: dt.date,
        end_date: dt.date,
        brand_dictionary: Optional[list[str]] = None,
    ) -> SearchInsightReport:
        payload = {
            "customer_id": customer_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "brand_dictionary": brand_dictionary,
        }
        resp = self._http.post("/reports/search-insights", json=payload)
        resp.raise_for_status()
        return SearchInsightReport.model_validate(resp.json())

    def upload_business_outcomes(
        self,
        csv_content: str,
        customer_id: str,
        currency_code: str,
        timezone: str = "UTC",
        attribution_window_days: int = 30,
        conversion_definition: str = "purchase",
    ) -> BusinessOutcomeDataset:
        payload = {
            "csv_content": csv_content,
            "customer_id": customer_id,
            "currency_code": currency_code,
            "timezone": timezone,
            "attribution_window_days": attribution_window_days,
            "conversion_definition": conversion_definition,
        }
        resp = self._http.post("/ingestion/upload-csv", json=payload)
        resp.raise_for_status()
        return BusinessOutcomeDataset.model_validate(resp.json())

    def run_preflight_check(
        self, dataset_id: str, conversion_lag_days: int = 14
    ) -> DataQualityReport:
        payload = {"dataset_id": dataset_id, "conversion_lag_days": conversion_lag_days}
        resp = self._http.post("/diagnostics/preflight", json=payload)
        resp.raise_for_status()
        return DataQualityReport.model_validate(resp.json())

    def run_incrementality_diagnostic(
        self, dataset_id: str, conversion_lag_days: int = 14
    ) -> ObservationalDiagnosticResult:
        payload = {"dataset_id": dataset_id, "conversion_lag_days": conversion_lag_days}
        resp = self._http.post("/diagnostics/incrementality", json=payload)
        resp.raise_for_status()
        return ObservationalDiagnosticResult.model_validate(resp.json())

    def calculate_power(
        self,
        customer_id: str,
        baseline_daily_revenue: Decimal,
        baseline_revenue_cv: float,
        alpha: float = 0.05,
        power: float = 0.80,
        treatment_split: float = 0.50,
        target_test_days: int = 28,
        conversion_lag_days: int = 14,
    ) -> ExperimentPowerAnalysis:
        payload = {
            "customer_id": customer_id,
            "baseline_daily_revenue": float(baseline_daily_revenue),
            "baseline_revenue_cv": baseline_revenue_cv,
            "alpha": alpha,
            "power": power,
            "treatment_split": treatment_split,
            "target_test_days": target_test_days,
            "conversion_lag_days": conversion_lag_days,
        }
        resp = self._http.post("/experiments/power", json=payload)
        resp.raise_for_status()
        return ExperimentPowerAnalysis.model_validate(resp.json())

    def generate_experiment_design(
        self,
        customer_id: str,
        design_type: Literal["PLATFORM_NATIVE_SPLIT", "GEO_BASED_STEP_TEST"] = "GEO_BASED_STEP_TEST",
        test_duration_days: int = 28,
        pre_period_days: int = 28,
        conversion_lag_days: int = 14,
        power_mde_pct: float = 8.5,
    ) -> ExperimentPlan:
        payload = {
            "customer_id": customer_id,
            "design_type": design_type,
            "test_duration_days": test_duration_days,
            "pre_period_days": pre_period_days,
            "conversion_lag_days": conversion_lag_days,
            "power_mde_pct": power_mde_pct,
        }
        resp = self._http.post("/experiments/design", json=payload)
        resp.raise_for_status()
        return ExperimentPlan.model_validate(resp.json())

    def analyze_experiment(
        self,
        test_id: str,
        pre_period_start: dt.date,
        pre_period_end: dt.date,
        test_period_start: dt.date,
        test_period_end: dt.date,
        treat_pre_revenue: Decimal,
        treat_pre_spend: Decimal,
        treat_post_revenue: Decimal,
        treat_post_spend: Decimal,
        ctrl_pre_revenue: Decimal,
        ctrl_pre_spend: Decimal,
        ctrl_post_revenue: Decimal,
        ctrl_post_spend: Decimal,
        revenue_daily_stdev: float = 500.0,
    ) -> ExperimentResultAnalysis:
        payload = {
            "test_id": test_id,
            "pre_period_start": pre_period_start.isoformat(),
            "pre_period_end": pre_period_end.isoformat(),
            "test_period_start": test_period_start.isoformat(),
            "test_period_end": test_period_end.isoformat(),
            "treat_pre_revenue": float(treat_pre_revenue),
            "treat_pre_spend": float(treat_pre_spend),
            "treat_post_revenue": float(treat_post_revenue),
            "treat_post_spend": float(treat_post_spend),
            "ctrl_pre_revenue": float(ctrl_pre_revenue),
            "ctrl_pre_spend": float(ctrl_pre_spend),
            "ctrl_post_revenue": float(ctrl_post_revenue),
            "ctrl_post_spend": float(ctrl_post_spend),
            "revenue_daily_stdev": revenue_daily_stdev,
        }
        resp = self._http.post("/experiments/analyze", json=payload)
        resp.raise_for_status()
        return ExperimentResultAnalysis.model_validate(resp.json())

    def calculate_breakeven_hurdle(
        self,
        contribution_margin_rate: Decimal,
        notes: Optional[list[str]] = None,
    ) -> EconomicHurdleResult:
        payload = {
            "contribution_margin_rate": float(contribution_margin_rate),
            "notes": notes,
        }
        resp = self._http.post("/economics/breakeven", json=payload)
        resp.raise_for_status()
        return EconomicHurdleResult.model_validate(resp.json())

    def create_contract_from_delivery(self, report: DeliveryReport) -> DecisionContract:
        resp = self._http.post("/contracts/from-delivery", json=report.model_dump(mode="json"))
        resp.raise_for_status()
        return DecisionContract.model_validate(resp.json())

    def get_contract(self, contract_id: str) -> DecisionContract:
        resp = self._http.get(f"/contracts/{contract_id}")
        resp.raise_for_status()
        return DecisionContract.model_validate(resp.json())
