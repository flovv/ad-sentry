# PMax Sentry — System Architecture

## Overview

**PMax Sentry** provides rigorous Performance Max delivery observability, data quality preflight, and causal incrementality measurement.

The architecture enforces a strict evidence discipline moving across three stages:

1. **Delivery Observability (Free / Open-Source):**
   - Summarizes reported PMax performance across channels and ad formats using supported Google Ads API v26 segments.
   - Compares segmented delivery against unsegmented campaign totals to perform transparent reconciliation.
   - Separate search demand insights report without fabricated spend.

2. **Historical Diagnosis (Pro):**
   - Connects advertising activity with daily business outcome metrics.
   - Applies preflight data quality checks (sample size, continuity, conversion lag maturation, spend variance).
   - Reports observational associations and uncertainty intervals, with explicit documentation of assumptions and omitted controls.
   - Does *not* infer cannibalization or causal lift from historical observational correlation alone.

3. **Causal Validation (Pro):**
   - Helps advertisers design and evaluate randomized or geo-based incrementality experiments.
   - Calculates statistical power and Minimum Detectable Effect (MDE) dynamically from account baseline variance and conversion lag, rather than arbitrary fixed defaults.
   - Analyzes completed experiment results via Difference-in-Differences (DiD) with 95% confidence intervals and hypothesis testing.
   - Formulates advertiser break-even hurdles based on contribution economics ($1 / \mu$).

## Repository Structure

```text
pmax-auditor-suite/
├── packages/
│   ├── pmax_sentry_core/          # Open-source schemas, API client, normalization, reconciliation
│   ├── pmax_sentry_cli/           # Open-source CLI (command: pmax-audit)
│   ├── pmax_sentry_mcp/           # Read-only Model Context Protocol (MCP) server
│   └── pmax_sentry_pro/           # Commercial thin client for hosted Pro API
├── apps/
│   ├── pro_api/                   # Hosted FastAPI service, tenant isolation, report jobs
│   └── pro_web/                   # Web dashboard and self-service reports
├── services/
│   ├── data_ingestion/            # CSV and connector intake and strict validation
│   ├── data_quality/              # Preflight checks (lag maturation, continuity, variance)
│   ├── incrementality/            # Observational diagnostics, power analysis, DiD, economics
│   └── decision_contracts/       # Structured decision contract generation and JSON schemas
├── schemas/
│   ├── delivery_report.schema.json
│   └── decision_contract.schema.json
├── docs/
└── pyproject.toml
```

## Security & Tenant Boundary

- **Read-Only API in v1:** PMax Sentry does not contain mutate operations or write credentials for campaign bidding or targeting.
- **Tenant Isolation:** Every workspace has isolated data storage with complete customer disconnect and data deletion endpoints.
- **Log Sanitization:** 10-digit customer IDs, bearer tokens, revenue figures, and query text are sanitized from application logs.
