# Incrementality Experiment Design & Analysis Guide

## Dynamic Power Analysis

PMax Sentry rejects arbitrary fixed experiment defaults (such as a hardcoded 14-day duration or 4-cell ladder). Instead, statistical power is calculated from account-specific conditions:

$$\text{MDE} = (z_{1 - \alpha/2} + z_{1 - \beta}) \cdot \sqrt{\frac{(1/p) + (1/(1-p))}{T}} \cdot \text{CV}_{\text{revenue}}$$

Where:
- $\alpha = 0.05$ ($z_{1 - \alpha/2} = 1.96$)
- $1 - \beta = 0.80$ ($z_{1 - \beta} = 0.84$)
- $p$: Treatment allocation fraction (e.g. 0.50 for 50/50 split)
- $T$: Candidate test duration in days (typically 21 to 42 days)
- $\text{CV}_{\text{revenue}} = \frac{\sigma_{\text{revenue}}}{\bar{Y}_{\text{revenue}}}$: Baseline revenue volatility

### Total Study Duration

$$\text{Total Duration} = \text{Pre-Period} + \text{Test Period} + \text{Conversion Lag Maturation Window}$$

## Difference-in-Differences (DiD) Estimation

For a completed experiment with treatment arm and control counterfactual:

$$\Delta Y_{\text{treat}} = Y_{\text{treat, post}} - Y_{\text{treat, pre}}$$
$$\Delta Y_{\text{ctrl}} = Y_{\text{ctrl, post}} - Y_{\text{ctrl, pre}}$$
$$\text{Incremental Business Revenue} = \Delta Y_{\text{treat}} - \Delta Y_{\text{ctrl}}$$

$$\Delta S_{\text{treat}} = S_{\text{treat, post}} - S_{\text{treat, pre}}$$
$$\Delta S_{\text{ctrl}} = S_{\text{ctrl, post}} - S_{\text{ctrl, pre}}$$
$$\text{Incremental Media Spend} = \Delta S_{\text{treat}} - \Delta S_{\text{ctrl}}$$

$$\text{measured iROAS} = \frac{\text{Incremental Business Revenue}}{\text{Incremental Media Spend}}$$

Standard errors and 95% confidence intervals are computed using the pooled variance of the daily difference series.
