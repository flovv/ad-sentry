---
name: pmax-delivery-audit
description: Audit and reconcile Google Ads Performance Max (PMax) delivery mix across channels and formats, inspect search demand categories, calculate contribution-margin break-even hurdles (1/mu), run data quality preflights on business revenue data, and generate client-ready agency pitch decks.
version: 0.1.0
author: flovv, Hermes Agent
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [google-ads, performance-max, pmax, roas, iroas, incrementality, search-insights, reconciliation, break-even, agency-audit, polar]
    related_skills: []
---

# Performance Max Delivery & Incrementality Audit Skill (`pmax-delivery-audit`)

Audits Google Ads Performance Max delivery, reconciles campaign totals against segmented delivery, evaluates search-demand volume, and determines business break-even economics:

- **Free Open-Core (`pmax-sentry`):** PMax channel (Search, Partners, Display, YouTube, Discover, Gmail, Maps) and format (product feed, video) segmentation via API v26, unsegmented total vs. segmented cost reconciliation (raw difference, coverage ratio, zero hidden residuals), and search demand insight categories (volume, clicks, conversions without cost metrics).
- **PMax Sentry Pro (`pmax-sentry-pro`):** Business outcome data quality preflight (sample size, continuity, conversion lag maturation, spend variance), observational regression diagnostic, dynamic power analysis & MDE, causal Difference-in-Differences (DiD) experiment evaluation, and standalone White-Label HTML/PDF Pitch Decks for agency client presentations.

> [!IMPORTANT]
> **Division of Responsibilities:**
> - **The Engine (`pmax_sentry_core`, `services`, `pmax-audit`) calculates all arithmetic:** Never perform manual spend subtractions, invented cannibalization math, or ad-hoc regressions in LLM prose. Always call `fetch_pmax_delivery()`, `calculate_breakeven_hurdle()`, `run_data_quality_preflight()`, or the `pmax-audit` CLI.
> - **The Agent explains results within evidence boundaries:** Distinguish strictly between `REPORTED` (platform-attributed), `OBSERVATIONAL` (historical correlation), and `EXPERIMENTAL` (causal lift). Never claim a residual correlation proves cannibalization or waste without experimental validation.
> - **Workspace hygiene:** Avoid unconstrained recursive file scans. Use targeted commands.

---

## Pro Licensing & Availability

Check whether PMax Sentry Pro is installed:
```python
import pmax_sentry_pro
from pmax_sentry_pro._auth import verify_license
```

Pro features (White-Label Deck export, business data ingestion, causal validation) accept a license key:
- **Environment Variable:** `os.environ["PMAX_API_KEY"] = "PMAX_PRO_..."`
- **Evaluation / Local Dev Key:** For testing or evaluation without live Polar credentials, pass `PMAX_TEST_AGENCY_PRO_KEY_12345` or `PMAX_TEST_SINGLE_PASS_KEY_12345`.
- **Purchase:** Keys are available via Polar.sh at `https://polar.sh/pmax-sentry`.

---

## Analysis Workflows & CLI Commands

### 1. Delivery Mix & Reconciliation Audit (Terminal / JSON / CSV)
Inspect how PMax is allocating spend across Google networks and format types:

```bash
# Terminal view with delivery mix and reconciliation audit
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30

# Export clean CSV
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 --format csv -o pmax_delivery.csv
```

**Key Diagnostic Elements to Highlight to User:**
1. **Orthogonal Formats:** Video and Merchant Center product feed units appear across multiple channels. They are not independent channels.
2. **Reconciliation Audit:** Compares total campaign cost against segmented sum.
   - Status `COMPLETE`: Reconciles within 0.1% tolerance.
   - Status `PARTIAL`: Shows exact `difference_micros` and `coverage_ratio`.
   - Never masked with artificial formulas; unexplained differences are **never** attributed to "Display", "Video", or "waste".

---

### 2. Search Demand Insights (Demand vs. Spend)
Inspect consumer search categories triggering PMax ads:

```bash
pmax-audit insights --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 -b "brand" -b "brandname"
```

> [!WARNING]
> Search-term insights represent **search demand** (clicks, impressions, search volume, conversions). They **never contain ad spend**.
> Never subtract category values to calculate brand-search spend.

---

### 3. Contribution Margin & Break-Even Hurdle ($1 / \mu$)
Ask the user for their contribution margin rate $\mu$ before media cost (accounting for COGS, shipping, payment processing, returns):

```python
from services.incrementality.economics import calculate_breakeven_hurdle

# Example: 35% contribution margin rate
hurdle = calculate_breakeven_hurdle(0.35)
print(f"Break-Even iROAS: {hurdle.breakeven_iroas:.2f}x")  # 2.86x
```

**Strategic Guidance for the Agent:**
- Explain to the advertiser: *„Bei einer Marge von 35% muss jeder zusätzliche PMax-Euro mindestens 2,86 € inkrementellen Mehrumsatz generieren, um kostendeckend zu sein. Liegt der marginale Zuwachs darunter, verbrennt die Skalierung Geld – selbst wenn Google Ads einen durchschnittlichen Kampagnen-ROAS von 3.50x meldet.“*

---

### 4. Client-Ready White-Label Pitch Deck (For Agencies)
Generate a standalone, interactive HTML deck with custom branding for client pitches and executive reviews:

```bash
pmax-audit report \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-30 \
  --deck client_audit_deck.html \
  --agency "Nexus Performance Media" \
  --brand "Northwind Retail" \
  --margin 0.35
```

The generated HTML deck features:
- Agency Name & Logo
- Executive KPI Cards (Total Spend, Attributed Value, Reported ROAS, Break-Even Hurdle)
- Interactive Channel Distribution table with visual percentage bars
- Transparent Reconciliation Audit with diagnostic notes
- Search Demand Insight Categories
- Formal Decision Contract with documented assumptions and next review milestones.

---

### 5. Historical Business Revenue Ingestion & Data Quality Preflight
When the user supplies daily business outcome data (total revenue, organic revenue, promo flags):

```python
from services.data_ingestion.validator import parse_business_outcomes_csv
from services.data_quality.preflight import run_data_quality_preflight
from services.incrementality.diagnostic import run_incrementality_diagnostic

# 1. Parse CSV
dataset = parse_business_outcomes_csv(csv_text, customer_id="1234567890", currency_code="USD")

# 2. Preflight Quality Check
preflight = run_data_quality_preflight(dataset, lag_days=14)
if not preflight.eligible_for_observational:
    print(f"Data quality warning: {preflight.reasons}")
else:
    # 3. Observational Diagnostic
    diag = run_incrementality_diagnostic(dataset, lag_days=14)
    print(f"Modeled iROAS: {diag.modeled_iroas_estimate.formatted}")
```

---

## Agent Response Template (Copy-Paste Ready for User Conversations)

When a user asks: *"Audit my Performance Max campaign"*, structure your response as follows:

1. **Executive Snapshot:**
   - Audited Period, Account Currency, Total Reported PMax Spend.
   - Platform-Attributed Conversion Value & Reported ROAS.
2. **Channel & Format Distribution:**
   - Table of spend shares (Search vs. Product Feed Shopping vs. YouTube vs. Display).
   - Format flags (Merchant Center feed utilization, Video asset deployment).
3. **Reconciliation Audit:**
   - State whether the segmented rows reconcile with campaign totals (`COMPLETE` or `PARTIAL`).
   - Disclose raw discrepancy if present without assigning unproven blame.
4. **Economics & Hurdle Analysis:**
   - Prompt the user for their contribution margin rate if unknown.
   - Compute and display the $\text{Break-Even iROAS} = 1/\mu$.
5. **Actionable Next Step / Agency Pitch Deck Offer:**
   - Offer to generate a client-facing White-Label HTML Audit Deck or formulate an incrementality experiment design.
