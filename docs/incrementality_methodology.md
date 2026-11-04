# Incrementality Methodology & Evidence Discipline

## Evidence Hierarchy

PMax Sentry categorizes all metrics and diagnostic claims into three unambiguous evidence classes:

1. **REPORTED:**
   - Platform-attributed values (impressions, clicks, cost, attributed conversions, attributed conversion value).
   - Metrics are subject to platform conversion definitions, attribution windows, and view-through/data-driven attribution modeling.
   - **Label:** `platform-reported ROAS` = $\frac{\text{Attributed Value}}{\text{Platform Ad Spend}}$.

2. **OBSERVATIONAL:**
   - Historical time-series regression estimates linking ad spend to total realized business outcomes, with explicit covariates (non-PMax spend, promotions, stock constraints).
   - Requires preflight quality gates (minimum 30 continuous days, conversion lag maturation, spend variance $CV \ge 0.05$).
   - **Label:** `modeled iROAS estimate` accompanied by 95% confidence intervals and visible assumptions.
   - Associations with organic/direct revenue are reported as `association diagnostics`. They are **never** labeled causal "cannibalization proof".

3. **EXPERIMENTAL:**
   - Causal incrementality estimates derived from prospective randomized or geo-based intervention experiments.
   - Analyzed via Difference-in-Differences (DiD) against pre-period and holdout counterfactuals.
   - **Label:** `measured iROAS` accompanied by hypothesis tests and statistical power disclosures.

## The Pitfalls of Naive Observational Models

As established in literature (Gordon et al., 2019, *A Comparison of Approaches to Advertising Measurement*), observational regressions on advertising time series frequently deviate substantially from randomized experimental baselines due to:
- Endogenous bidding (bidding systems naturally bid more aggressively when underlying consumer demand is high).
- Simultaneous marketing campaigns (promotions, email blasts, PR spikes).
- Conversion lag and immature conversion maturation windows.

PMax Sentry prevents misleading advertisers by refusing to run observational models when data quality fails, and always routing accounts to prospective experiments when causal lift or marginal adjustments are desired.
