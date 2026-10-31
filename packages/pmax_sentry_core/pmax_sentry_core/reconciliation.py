from __future__ import annotations

from decimal import Decimal
from typing import Sequence
from pmax_sentry_core.models import CoverageSummary, DeliveryRow


def reconcile_delivery(
    segmented_rows: Sequence[DeliveryRow],
    unsegmented_cost_micros: int,
    tolerance_pct: float = 0.001,  # 0.1% tolerance
) -> CoverageSummary:
    """
    Reconciles segmented PMax delivery metrics against unsegmented campaign totals.

    Adheres strictly to the specification:
    - Calculates raw difference: unsegmented_cost_micros - segmented_cost_micros.
    - NEVER hides differences with max(0, residual).
    - NEVER labels an unexplained difference 'Display', 'Video', or 'waste'.
    - Returns COMPLETE if within tolerance, PARTIAL if segmented cost differs beyond tolerance,
      or UNAVAILABLE if unsegmented or segmented data is missing or zero when the other is positive.
    """
    segmented_cost_micros = sum(r.cost_micros for r in segmented_rows)
    raw_diff = unsegmented_cost_micros - segmented_cost_micros
    reasons: list[str] = []

    if unsegmented_cost_micros == 0:
        if segmented_cost_micros == 0:
            coverage_ratio = Decimal("1.0")
            status = "COMPLETE"
            reasons.append("Zero spend reported for both unsegmented and segmented queries.")
        else:
            coverage_ratio = None
            status = "PARTIAL"
            reasons.append(
                f"Segmented cost is {segmented_cost_micros} micros but unsegmented total is 0."
            )
        return CoverageSummary(
            status=status,
            segmented_cost_micros=segmented_cost_micros,
            unsegmented_cost_micros=unsegmented_cost_micros,
            difference_micros=raw_diff,
            coverage_ratio=coverage_ratio,
            reasons=reasons,
        )

    ratio = Decimal(segmented_cost_micros) / Decimal(unsegmented_cost_micros)

    if segmented_cost_micros == 0:
        status = "UNAVAILABLE"
        reasons.append(
            f"Segmented query returned 0 micros while campaign total reported {unsegmented_cost_micros} micros. "
            "PMax segmentation data is unavailable or not returned by Google Ads API for this window."
        )
    elif abs(float(ratio) - 1.0) <= tolerance_pct:
        status = "COMPLETE"
        reasons.append(
            f"Segmented cost ({segmented_cost_micros:,} micros) reconciles with total ({unsegmented_cost_micros:,} micros) "
            f"within {(tolerance_pct * 100):.2f}% tolerance."
        )
    else:
        status = "PARTIAL"
        diff_pct = ((float(ratio) - 1.0) * 100)
        direction = "under-reported" if raw_diff > 0 else "over-reported"
        reasons.append(
            f"Segmented cost is {direction} by {abs(raw_diff):,} micros ({abs(diff_pct):.2f}% discrepancy). "
            f"Coverage ratio is {ratio:.4f}. This difference is preserved as unclassified discrepancy; "
            "it is never assumed to belong to any specific channel, format, or residual category."
        )

    return CoverageSummary(
        status=status,
        segmented_cost_micros=segmented_cost_micros,
        unsegmented_cost_micros=unsegmented_cost_micros,
        difference_micros=raw_diff,
        coverage_ratio=ratio.quantize(Decimal("0.0001")),
        reasons=reasons,
    )
