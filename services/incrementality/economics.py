from __future__ import annotations

from decimal import Decimal
from services.incrementality.models import EconomicHurdleResult


def calculate_breakeven_hurdle(
    contribution_margin_rate: Decimal | float,
    notes: list[str] | None = None,
) -> EconomicHurdleResult:
    """
    Calculates the advertiser's economic break-even incremental ROAS hurdle.

    Adheres strictly to Section 4.4 and Section 7.5:
    - Break-even iROAS = 1 / mu
    - Profit-maximizing spend is where MARGINAL iROAS reaches 1 / mu.
    - Never extrapolates an untested response curve or confuses average ROAS with marginal return.
    """
    mu = Decimal(str(contribution_margin_rate))
    if mu <= Decimal(0) or mu > Decimal(1):
        raise ValueError(f"Contribution margin rate mu must be in (0.0, 1.0], got {mu}")

    hurdle = (Decimal(1) / mu).quantize(Decimal("0.01"))

    assumptions = [
        f"Contribution margin rate mu = {mu:.1%} accounts for all variable costs (COGS, payment processing, packaging, fulfillment, returns).",
        "Outcome variable is total incremental business revenue.",
        "Break-even condition: Incremental Net Profit = 0 => (Incremental Revenue * mu) - Incremental Spend = 0.",
    ]
    if notes:
        assumptions.extend(notes)

    guidance = (
        f"To break even on an incremental dollar of ad spend, PMax must generate at least ${hurdle:.2f} of incremental revenue. "
        f"Advertiser profit increases as long as marginal iROAS > {hurdle:.2f}x. "
        "Notice that platform-reported average ROAS does NOT identify this point. "
        "A formal marginal response curve requires multi-spend experimental interventions."
    )

    return EconomicHurdleResult(
        contribution_margin_rate=mu,
        breakeven_iroas=hurdle,
        formula="Break-even iROAS = 1 / mu",
        units="Incremental Revenue / Incremental Spend",
        input_source="Advertiser-supplied contribution economics",
        scenario_assumptions=assumptions,
        marginal_spend_guidance=guidance,
    )


def calculate_incremental_net_profit(
    incremental_revenue: Decimal,
    incremental_spend: Decimal,
    contribution_margin_rate: Decimal,
) -> Decimal:
    """
    Computes incremental net profit: (Incremental Revenue * mu) - Incremental Media Spend.
    """
    return ((incremental_revenue * contribution_margin_rate) - incremental_spend).quantize(Decimal("0.01"))
