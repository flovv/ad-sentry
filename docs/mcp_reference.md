# Model Context Protocol (MCP) Reference

The `pmax-sentry-mcp` package exposes 11 deterministic, read-only tools for AI assistants connecting via Model Context Protocol:

## Tool Surface

1. **`list_accessible_customers()`**
   Lists accessible customer accounts with name, currency code, and timezone.

2. **`list_pmax_campaigns(customer_id: str)`**
   Lists eligible PMax campaigns, status, bidding strategy, and target ROAS.

3. **`fetch_pmax_delivery_report(customer_id: str, start_date: str, end_date: str)`**
   Fetches reported delivery mix (channel × format dimensions) with unsegmented total reconciliation.

4. **`fetch_search_demand_insights(customer_id: str, start_date: str, end_date: str, brand_dictionary: list[str] | None)`**
   Fetches search term categories with demand metrics (clicks, volume, conversions). Never requests or reports cost metrics.

5. **`validate_business_outcomes(customer_id: str, csv_content: str, currency_code: str, timezone: str)`**
   Validates daily business outcome upload and runs preflight quality checks (continuity, sample size, lag, variance).

6. **`run_incrementality_diagnostic(customer_id: str, csv_content: str, currency_code: str, conversion_lag_days: int)`**
   Executes observational regression diagnostic. Returns modeled iROAS estimate with 95% confidence intervals and organic sensitivity. Declares evidence class: OBSERVATIONAL.

7. **`calculate_contribution_margin_hurdle(contribution_margin_rate: float)`**
   Calculates break-even incremental ROAS hurdle: $1 / \mu$.

8. **`assess_experiment_readiness(customer_id: str, baseline_daily_revenue: float, baseline_revenue_cv: float, test_days: int, conversion_lag_days: int)`**
   Computes statistical power and Minimum Detectable Effect (MDE) dynamically.

9. **`analyze_completed_experiment_results(...)`**
   Computes causal Difference-in-Differences (DiD) estimate for completed experiment. Declares evidence class: EXPERIMENTAL.

10. **`propose_experiment_design(customer_id: str, design_type: str, test_duration_days: int, lag_days: int, power_mde_pct: float)`**
    Generates experiment protocol (treatment/control units, allowable campaign changes, contamination risks, stop conditions).

11. **`generate_decision_contract(customer_id: str, contract_type: str, payload_json: str)`**
    Generates structured JSON decision contract. Requires explicit human confirmation; live mutations are disabled.

## Starting the Server

```bash
pmax-mcp
# or via python:
python -m pmax_sentry_mcp.server
```
