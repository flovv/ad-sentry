from __future__ import annotations

import datetime as dt
from decimal import Decimal
import numpy as np
from scipy import stats

from services.data_ingestion.models import BusinessOutcomeDataset
from services.data_quality.preflight import run_data_quality_preflight
from services.incrementality.models import (
    AssociationDiagnostic,
    EvidenceClass,
    ObservationalDiagnosticResult,
    UncertaintyInterval,
)


def run_incrementality_diagnostic(
    dataset: BusinessOutcomeDataset,
    lag_days: int = 14,
) -> ObservationalDiagnosticResult:
    """
    Runs observational incrementality diagnostic on matured historical data.

    Adheres strictly to the specification:
    - Never fabricates numbers. If data quality fails, returns INSUFFICIENT_DATA.
    - Labels output as modeled iROAS estimate with visible 95% confidence intervals and assumptions.
    - Reports organic sensitivity as an association diagnostic, never proof of cannibalization.
    """
    preflight = run_data_quality_preflight(dataset, lag_days=lag_days)

    total_spend = dataset.total_pmax_cost
    total_conv_val = sum((r.pmax_conversion_value for r in dataset.records), Decimal(0))
    platform_reported_roas = (total_conv_val / total_spend) if total_spend > Decimal(0) else Decimal("0")

    if not preflight.eligible_for_observational:
        return ObservationalDiagnosticResult(
            status="INSUFFICIENT_DATA",
            evidence_class=EvidenceClass.OBSERVATIONAL,
            model_version="1.0.0-ols-covariates",
            dataset_id=dataset.dataset_id,
            matured_date_window=(dataset.start_date or dt.date.today(), dataset.end_date or dt.date.today()),
            platform_reported_roas=platform_reported_roas.quantize(Decimal("0.01")),
            assumptions=["Requires at least 30 continuous days of matured business outcome data."],
            limitations=preflight.reasons,
        )

    # Filter matured records
    cutoff = preflight.matured_date_cutoff
    matured = [r for r in dataset.records if r.date <= cutoff]
    matured.sort(key=lambda r: r.date)

    start_matured = matured[0].date
    end_matured = matured[-1].date

    # Build feature matrices
    y_rev = np.array([float(r.total_business_revenue) for r in matured])
    x_pmax = np.array([float(r.pmax_cost) for r in matured])

    # Covariates
    controls_included: list[str] = []
    omitted_controls: list[str] = []

    X_cols = [np.ones_like(x_pmax), x_pmax]

    # Check non_pmax_spend
    has_non_pmax = any(r.non_pmax_spend is not None for r in matured)
    if has_non_pmax:
        non_pm = np.array([float(r.non_pmax_spend or 0) for r in matured])
        if np.std(non_pm) > 1e-4:
            X_cols.append(non_pm)
            controls_included.append("non_pmax_media_spend")
        else:
            omitted_controls.append("non_pmax_media_spend (zero variance)")
    else:
        omitted_controls.append("non_pmax_media_spend (untracked)")

    # Check promo_active
    has_promo = any(r.promo_active for r in matured) and not all(r.promo_active for r in matured)
    if has_promo:
        promo = np.array([1.0 if r.promo_active else 0.0 for r in matured])
        X_cols.append(promo)
        controls_included.append("promotional_flag")
    else:
        omitted_controls.append("promotional_calendar (no variation)")

    # Check stock_constrained
    has_stock = any(r.stock_constrained for r in matured) and not all(r.stock_constrained for r in matured)
    if has_stock:
        stock = np.array([1.0 if r.stock_constrained else 0.0 for r in matured])
        X_cols.append(stock)
        controls_included.append("stock_out_flag")
    else:
        omitted_controls.append("inventory_stock_data (untracked)")

    X = np.column_stack(X_cols)
    n, k = X.shape

    # OLS estimation
    try:
        XtX_inv = np.linalg.pinv(X.T @ X)
        beta = XtX_inv @ (X.T @ y_rev)
        residuals = y_rev - (X @ beta)
        rss = float(np.sum(residuals**2))
        tss = float(np.sum((y_rev - np.mean(y_rev)) ** 2))
        r_squared = max(0.0, 1.0 - (rss / tss)) if tss > 0 else 0.0

        # Degrees of freedom and variance
        df = max(1, n - k)
        sigma2 = rss / df
        cov_beta = sigma2 * XtX_inv
        se_pmax = float(np.sqrt(max(1e-12, cov_beta[1, 1])))

        pmax_coef = float(beta[1])
        t_stat = pmax_coef / se_pmax
        p_val = 2.0 * float(1.0 - stats.t.cdf(abs(t_stat), df=df))

        # 95% Confidence Interval
        t_crit = float(stats.t.ppf(0.975, df=df))
        ci_low = max(0.0, pmax_coef - (t_crit * se_pmax))
        ci_high = pmax_coef + (t_crit * se_pmax)

        iroas_interval = UncertaintyInterval(
            point_estimate=Decimal(str(round(pmax_coef, 2))),
            ci_lower_95=Decimal(str(round(ci_low, 2))),
            ci_upper_95=Decimal(str(round(ci_high, 2))),
        )
    except Exception as e:
        return ObservationalDiagnosticResult(
            status="INSUFFICIENT_DATA",
            evidence_class=EvidenceClass.OBSERVATIONAL,
            model_version="1.0.0-ols-covariates",
            dataset_id=dataset.dataset_id,
            matured_date_window=(start_matured, end_matured),
            platform_reported_roas=platform_reported_roas.quantize(Decimal("0.01")),
            assumptions=["Linear observational response"],
            limitations=[f"Numerical estimation failure: {e}"],
        )

    # Association diagnostic for organic revenue
    assoc_diag: AssociationDiagnostic | None = None
    has_organic = any(r.organic_revenue is not None for r in matured)
    if has_organic:
        y_org = np.array([float(r.organic_revenue or 0) for r in matured])
        if np.std(y_org) > 1e-4:
            beta_org = XtX_inv @ (X.T @ y_org)
            res_org = y_org - (X @ beta_org)
            sigma2_org = float(np.sum(res_org**2)) / df
            se_org = float(np.sqrt(max(1e-12, sigma2_org * XtX_inv[1, 1])))
            org_coef = float(beta_org[1])
            t_org = org_coef / se_org
            p_org = 2.0 * float(1.0 - stats.t.cdf(abs(t_org), df=df))

            assoc_diag = AssociationDiagnostic(
                metric_name="Organic/Direct Revenue Association with PMax Spend",
                coefficient=Decimal(str(round(org_coef, 3))),
                p_value=round(p_org, 4),
                interpretation=(
                    f"A $1.00 increase in PMax spend is associated with a ${org_coef:+.2f} change in organic revenue "
                    f"in historical time-series data (p={p_org:.3f})."
                ),
            )

    # Confidence evaluation
    status: Literal["COMPLETED", "LOW_CONFIDENCE", "INSUFFICIENT_DATA"] = "COMPLETED"
    reasons: list[str] = []
    if p_val > 0.15 or r_squared < 0.10:
        status = "LOW_CONFIDENCE"
        reasons.append(
            f"High observational uncertainty: p-value is {p_val:.3f} and model R² is {r_squared:.2f}. "
            "Historical variation cannot cleanly isolate incremental ad response from baseline demand."
        )

    return ObservationalDiagnosticResult(
        status=status,
        evidence_class=EvidenceClass.OBSERVATIONAL,
        model_version="1.0.0-ols-covariates",
        dataset_id=dataset.dataset_id,
        matured_date_window=(start_matured, end_matured),
        modeled_iroas_estimate=iroas_interval,
        platform_reported_roas=platform_reported_roas.quantize(Decimal("0.01")),
        r_squared=round(r_squared, 3),
        p_value=round(p_val, 4),
        association_diagnostic=assoc_diag,
        controls_included=controls_included,
        omitted_controls=omitted_controls,
        assumptions=[
            "Linear relation between ad spend and total revenue over observed historical spend window.",
            "Conversion maturation lag is fixed at the declared threshold.",
            "Unobserved confounding variables (seasonality, competitor activity) are assumed uncorrelated with spend.",
        ],
        limitations=reasons
        + [
            "Observational associations reflect historical correlation and bidding behavior, not randomized causal proof.",
            "Gordon et al. (2019) demonstrated that observational methods frequently deviate from causal experimental lift.",
        ],
    )
