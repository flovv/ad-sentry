# PMax Sentry — Developer Specification

**Document status:** Product and implementation specification for the first build  
**Updated:** 2026-10-31  
**Product names:** Free developer tool: **pmax-sentry**. Commercial service: **pmax-sentry-pro**.

## 1. Product decision

PMax Sentry helps advertisers inspect Performance Max delivery and assess whether reported results appear incremental to business outcomes.

The product moves through three evidence stages:

1. **Delivery observability (Free):** Read Google Ads reporting data and summarize reported PMax performance by channel and ad format.
2. **Historical diagnosis (Pro):** Join ad activity to business outcomes, assess data quality, and report observational associations with their assumptions and limits.
3. **Causal validation (Pro):** Help the user design and analyze an appropriate experiment. Reserve measured incremental outcomes and marginal-profit decisions for evidence that supports them.

These are evidence gates, not guaranteed outputs. If the account lacks suitable data or experimental power, the service must say so and stop short of a causal or optimization claim.

The free package is a local CLI and Python library. Pro is a hosted service with a thin Python/MCP client. Pro calculations and account data stay in the service; the client package does not contain the commercial modeling engine.

### Product promise

> See how PMax is reporting delivery, understand what the available data can and cannot establish, and decide what to investigate next.

The product must not infer waste or causal lift from channel mix alone.

## 2. Product scope

### Free tier: pmax-sentry

An open-source, local tool for analysts and developers. It provides:

- PMax campaign totals and daily performance.
- Channel and format reporting using Google Ads API segmentation.
- CSV and JSON exports with account currency, date window, API version, and data coverage.
- Optional search-demand insight reports, clearly separated from spend allocation.
- Reconciliation checks between total and segmented campaign reporting.

It does not calculate cannibalization, incremental ROAS, profit impact, or an optimal tROAS.

### Pro tier: pmax-sentry-pro

A hosted, read-only measurement service for advertisers, agencies, and analysts. It provides:

- OAuth-based Google Ads account connection and multi-account workspaces.
- Business outcome data ingestion through supported connectors or validated CSV upload.
- Data quality checks and an observational incrementality diagnostic.
- Experiment readiness, planning, and result analysis for accounts where a suitable design is feasible.
- Contribution-margin and break-even scenarios using advertiser-supplied economics.
- Evidence-linked reports and decision contracts.
- Optional MCP tools for compatible AI assistants.

Pro does not automatically change bids, budgets, or campaign settings in v1.

## 3. Feature matrix

| Capability | Free: pmax-sentry | Pro: pmax-sentry-pro |
| --- | --- | --- |
| Google Ads authentication | Local user configuration | Hosted OAuth account connection |
| PMax campaign totals | Yes | Yes |
| Channel reporting | Channel dimension and reported metrics | Historical, multi-account channel reporting |
| Format reporting | Product-data and video segments | Historical channel × format analysis |
| Search-demand insights | Optional category metrics | Joined to account and business context where supported |
| Brand classification | User-supplied rules for visible query data only | Versioned rules plus data coverage diagnostics |
| Business revenue data | No | Connector or validated upload |
| Incrementality | No | Observational diagnostic; experimental estimate when supported |
| Experiment workflow | No | Readiness and design; result analysis when outcome data is supplied |
| Profit / margin scenarios | No | Break-even hurdle using user-provided contribution margin and outcome definition |
| Marginal response curve | No | Only from suitable intervention data; no ordinary time-series extrapolation |
| Optimization | No | Scenario analysis only when evidence and response curve support it |
| Reports | Terminal, CSV, JSON | Interactive report, PDF export, JSON decision contract |
| Account mutations | Never | Not in v1 |

## 4. Reporting model and terminology

### 4.1 Channel and format are separate dimensions

Represent PMax delivery using the reported channel dimension and format flags:

- Channel: Google Search, Search Partners, Display, YouTube, Discover, Gmail, Maps, or another value returned by the API.
- Format flags: ads using product data and ads using video.

Product-data ads and video ads can appear across channels. The report must preserve the channel × format dimensions and must not add overlapping format totals as if they were independent channel buckets.

Use the label **reported delivery mix** for this output. Do not call it a full accounting of all underlying placements or auction inventory.

### 4.2 Search-demand insights are a separate report

Google Ads search-term insight data is a categorized view of search demand. It does not provide the cost field needed to calculate brand-search spend in the proposed table-subtraction design.

The product may report supported metrics such as clicks, conversions, conversion value, impressions, and search volume. It must not present these as brand/non-brand spend.

Brand classification is allowed only when the input source provides actual query text and an associated spend metric. The report must show:

- The source and date range.
- The classifier version and user-supplied brand dictionary.
- The share of query data that was classifiable.
- A separate unknown or unavailable amount where coverage is incomplete.

Do not infer a brand classification from a category label containing words such as “brand” or “self.”

### 4.3 Currency and time

- Read the customer account currency and timezone.
- Store money in integer micros or Decimal values with an explicit currency code.
- Do not label every account’s output as EUR.
- Make the reporting date range explicit.
- Preserve the source attribution settings and conversion definitions when available.
- Do not combine values from different currencies or attribution windows without an explicit conversion rule.

### 4.4 Economics and decision metrics

Keep platform attribution, causal lift, and advertiser profit as separate quantities:

- **Platform-reported ROAS:** platform-attributed conversion value divided by platform-reported ad spend, under the account’s conversion settings.
- **Incremental ROAS (iROAS):** experimentally estimated change in total business revenue divided by the corresponding change in ad spend, for a stated test and time window.
- **Incremental net profit:** incremental revenue multiplied by the applicable contribution-margin rate, less incremental media spend. The margin input must account for variable costs relevant to the chosen outcome, such as discounts, fulfillment, payment fees, and returns.

When the outcome is incremental revenue and `mu` is the contribution-margin rate before media cost, the break-even iROAS is `1 / mu`. A profit-maximizing spend point is where **marginal** iROAS reaches that hurdle; average ROAS does not identify that point. Show the formula, units, input source, and scenario assumptions beside any calculated hurdle.

Google documents Target ROAS as maximizing configured conversion value while averaging the target. That configured value can reflect the advertiser’s chosen conversion values, including profit-oriented values, but it does not by itself establish causal lift. Describe the product problem as a possible gap between configured/attributed value and the advertiser’s incremental profit objective. Do not claim that Google’s PMax objective is to maximize Google’s own revenue. [Google’s bid-strategy definitions](https://support.google.com/google-ads/answer/10969287?hl=en) and [Target ROAS API definition](https://developers.google.com/google-ads/api/reference/rpc/v26/MaximizeConversionValue) describe the supported product behavior.

The cited autobidding papers provide theoretical models under stated auction and objective assumptions. They do not establish the live PMax bid formula, guarantee full surplus extraction, or prove that high average-return inventory is deliberately used to subsidize low-return inventory. Keep any dual-bid equation or “subsidy” example in a clearly labeled theory appendix; never use it as production logic or as account-specific evidence.

## 5. Current Google Ads API integration

### 5.1 Versioning

Pin the Google Ads API client version in the service and CLI. The initial implementation should target the currently documented v26 API and put the API version in every report.

Before upgrading the API version, verify field compatibility and rerun the account-level reconciliation process. Do not silently fall back to older segmentation logic.

### 5.2 PMax performance query

Use the campaign resource and supported PMax segments rather than reconstructing spend through subtraction.

Illustrative GAQL query:

~~~sql
SELECT
  campaign.id,
  campaign.name,
  segments.date,
  segments.ad_network_type,
  segments.ad_using_product_data,
  segments.ad_using_video,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM campaign
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
  AND segments.date BETWEEN '2026-10-01' AND '2026-10-30'
~~~

The implementation must validate the exact field combinations against the pinned API version. Fetch an unsegmented campaign-total report separately and compare it with the segmented output.

### 5.3 Search insight query

Search insight output is informational and must not be used for spend subtraction.

Illustrative query shape:

~~~sql
SELECT
  campaign.id,
  campaign.name,
  campaign_search_term_insight.category_label,
  segments.date,
  metrics.clicks,
  metrics.conversions,
  metrics.conversions_value,
  metrics.impressions,
  metrics.search_volume
FROM campaign_search_term_insight
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
  AND segments.date BETWEEN '2026-10-01' AND '2026-10-30'
~~~

The query must not request metrics.cost_micros from this resource.

### 5.4 Authentication and access

- Local CLI users supply their own Google Ads API configuration and OAuth credentials.
- The CLI should support current client-library configuration and document legacy google-ads.yaml migration where needed.
- Pro uses an app-owned Google Cloud project and hosted OAuth consent flow. Do not ask each advertiser to create a local configuration file.
- Google Ads API access levels are managed through the Google Cloud project. The integration owner must maintain the required production access and permissible use.
- All v1 API calls are reporting calls. Do not import or expose mutate operations in the service.
- Multi-account access must use the account relationship and login-customer-id rules required by the API.

Official references:

- [PMax campaign reporting](https://developers.google.com/google-ads/api/performance-max/campaign-reporting)
- [Google Ads API v26 campaign_search_term_insight fields](https://developers.google.com/google-ads/api/fields/v26/campaign_search_term_insight)
- [Google Ads API access levels](https://developers.google.com/google-ads/api/docs/api-policy/access-levels?hl=en)
- [PMax channel definitions](https://support.google.com/google-ads/answer/16260129?hl=en)
- [PMax channel performance report](https://support.google.com/google-ads/answer/16260130?hl=en-GB)

## 6. Free package specification

### 6.1 CLI

Package name: **pmax-sentry**  
Command: **pmax-audit**

Initial commands:

~~~text
pmax-audit campaigns --customer-id 1234567890
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 --format csv
pmax-audit insights --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 --format json
~~~

The CLI must:

- Show a dry-run summary of the account, selected campaigns, dates, timezone, and currency before a large export.
- Keep account credentials out of command history, logs, and generated reports.
- Return clear errors for missing access, unsupported fields, no campaigns, partial data, and quota limits.
- Never print an estimated waste amount or causal claim.

### 6.2 Python API

Initial public interface:

~~~python
def fetch_pmax_delivery(
    customer_id: str,
    start_date: date,
    end_date: date,
    config_path: Path | None = None,
) -> DeliveryReport:
    ...
~~~

Keep API calls, normalization, reconciliation, and rendering in separate modules. The Python API must not require pandas for basic data retrieval; dataframe conversion can be an optional extra.

### 6.3 Core data contracts

~~~python
class DeliveryRow(BaseModel):
    customer_id: str
    campaign_id: str
    campaign_name: str
    date: date
    channel: str
    uses_product_data: bool | None
    uses_video: bool | None
    currency_code: str
    cost_micros: int
    impressions: int
    clicks: int
    conversions: Decimal
    conversion_value: Decimal

class CoverageSummary(BaseModel):
    status: Literal["COMPLETE", "PARTIAL", "UNAVAILABLE"]
    segmented_cost_micros: int
    unsegmented_cost_micros: int
    difference_micros: int
    coverage_ratio: Decimal | None
    reasons: list[str]

class DeliveryReport(BaseModel):
    schema_version: str
    api_version: str
    generated_at: datetime
    customer_id: str
    currency_code: str
    timezone: str
    start_date: date
    end_date: date
    rows: list[DeliveryRow]
    coverage: CoverageSummary
    warnings: list[str]
~~~

Use Pydantic v2. Validate numeric values, date ranges, customer IDs, currency, and API response completeness at the boundary.

### 6.4 Reconciliation

- Fetch totals and segmented metrics using the same date range, account, campaign set, and API version.
- Compare segmented cost against campaign totals.
- Store the raw difference and coverage ratio.
- If coverage is incomplete or metrics do not reconcile within a documented tolerance, mark the result PARTIAL and explain why.
- Do not hide negative or unexplained differences with max(0, residual).
- Do not label an unexplained difference “Display,” “Video,” or “waste.”

## 7. Pro measurement specification

### 7.1 Inputs

Pro incrementality analysis requires more than Google Ads data. The first release supports:

1. Google Ads campaign and channel data.
2. Daily business outcomes supplied through an approved connector or validated CSV upload.
3. Optional daily covariates such as promotions, prices, stock availability, and other media spend.

Minimum required fields for an observational diagnostic:

- Date and reporting timezone.
- Total business revenue or another agreed business outcome.
- Google Ads PMax spend and platform-reported conversion value.
- Conversion definitions and attribution window.
- Currency.
- Optional but strongly preferred: organic/direct outcomes, gross margin, promotion, stock, and non-PMax media activity.

Each connector must define its source fields, aggregation rules, known gaps, and retention period. Missing required inputs result in **INSUFFICIENT_DATA**, not a fabricated estimate.

### 7.2 Evidence classes

Every Pro result must declare one of these evidence classes:

- **REPORTED:** Directly returned by an advertising or commerce platform.
- **OBSERVATIONAL:** Model estimate from historical data; associations and assumptions are visible.
- **EXPERIMENTAL:** Incrementality estimate based on a valid randomized or geo-based experiment with a stated design and analysis.

Use **incremental ROAS** only with a named method, data window, and uncertainty interval. For an observational model, label it **modeled iROAS estimate** and display its assumptions. Use **measured iROAS** only for experimental evidence.

### 7.3 Modeling

Do not ship the current placeholder formulas.

The Pro model must:

- Separate business outcomes from platform-attributed conversions.
- Account for conversion lag and reporting delays.
- Test for missing periods, outliers, structural breaks, and insufficient variation.
- Include relevant controls available to the account and document omitted controls.
- Estimate uncertainty and report diagnostics.
- Compare model output to held-out time periods and, when available, experiment results.
- Return INSUFFICIENT_DATA or LOW_CONFIDENCE when the model is not suitable.
- Version the model, features, inputs, and transformations used for each result.

A residual relationship between PMax activity and organic/direct outcomes may be reported as an **association diagnostic**. It is not a causal estimate by itself. Do not turn a coefficient called kappa into a “cannibalization coefficient” without validation against experimental evidence.

### 7.4 Incrementality experiments

The product may help users plan and analyze a platform-native PMax experiment or a geo experiment when its estimand and implementation fit the account. Prefer a supported native experiment when it answers the question; use geo designs when business outcomes can be measured across suitable, sufficiently independent regions. The plan must describe:

- Treatment and control units.
- The estimand: what changes between arms, and which total business outcome the test is intended to measure.
- Required pre-period, test period, conversion-lag maturation, and any learning/ramp-up period.
- Power, minimum detectable effect, and allocation assumptions.
- Contamination risks.
- Allowed campaign changes during the test.
- Outcome metric and analysis method.
- Stop conditions and interpretation limits.

Do not hard-code a four-cell geo ladder or a 14-day duration. Choose the number of arms and duration from power, conversion volume and lag, learning behavior, and business seasonality. A tROAS step test must use properly separated treatment/control campaigns or another supported assignment method; it cannot be modeled as four independent settings on one campaign. Google’s GeoX guidance notes campaign duplication and learning considerations for heavy-up tests using Smart Bidding or cross-network formats. The planning report must link to the applicable implementation guidance and explain that setup changes are performed by the advertiser.

Experiment design and result estimation are separate from the descriptive channel report. Any requirement for an account mutation is out of scope for v1; the user receives a plan and performs approved changes in Google Ads. [PMax experiments](https://support.google.com/google-ads/answer/12997711?hl=en) and [Google GeoX implementation guidance](https://support.google.com/google-ads/answer/18073432?hl=en) are starting references, not a substitute for account-specific power and design checks.

### 7.5 Marginal returns and tROAS suggestions

Optimization is deferred until a validated response curve exists. Historical spend and revenue move in response to demand, seasonality, and the bidding system itself, so an ordinary time-series fit or spend elasticity is not a causal marginal curve.

A tROAS scenario may be generated only when:

- The input includes an experimentally supported spend-response estimate over the relevant spend range. A marginal curve generally requires multiple tested spend levels or repeated interventions; a single average-lift experiment is insufficient.
- The estimate is validated for the relevant account, outcome definition, and time window.
- The user supplies margin and business constraints.
- The uncertainty range is narrow enough for the declared decision threshold.
- The proposed setting stays within observed support; do not extrapolate an untested response curve to an exact tROAS floor.

When these conditions are not met, report a break-even scenario or experiment recommendation. Do not claim an optimal setting or convert an assumed spend/target relationship into a precise recommendation.

## 8. Decision contracts

A decision contract is a structured report object, not permission to execute a change.

Required fields:

~~~text
contract_version
account and campaign identifiers
date range and timezone
evidence class
claim and evidence references
reported metrics and units
estimate and uncertainty interval, if available
model version and diagnostics, if applicable
estimand and outcome definition, when applicable
experiment design, arms, dates, and analysis method, when applicable
power / minimum detectable effect and conversion-lag treatment, when applicable
contribution-margin input and break-even hurdle, when applicable
assumptions and known limitations
recommendation type: REVIEW, SCENARIO, EXPERIMENT, or NO_ACTION
approval_required: true
valid_until
next review or verification date, when applicable
data deletion / retention reference
~~~

In v1, contracts must not contain a live Google Ads mutation payload. Any future campaign change flow requires a separate authorization design, user confirmation, audit log, rollback plan, and explicit write permission.

## 9. Agentic and self-service workflow

The agent is a workflow orchestrator around typed, deterministic tools. It is not the numerical engine.

### User flow

1. User signs in and connects a Google Ads account in Pro, or supplies local credentials to the CLI.
2. The tool lists eligible PMax campaigns and asks the user to select the account and date range.
3. The agent checks access, currency, timezone, campaign data coverage, and available search insights.
4. The user receives the delivery report first. For an incrementality assessment, the agent requests business outcomes and confirms the outcome definition, attribution window, contribution margin, and known promotions or stock constraints.
5. A deterministic preflight checks data coverage, conversion lag, and experiment feasibility. It routes the account to an observational diagnostic, an experiment plan, or INSUFFICIENT_DATA.
6. Deterministic services calculate reports and diagnostics. For experiments, the user implements approved changes in Google Ads and later supplies or connects the matured outcome data for analysis.
7. The agent explains the report using only returned fields, evidence references, warnings, and assumptions. The user downloads or shares it. No campaign settings are changed.

### MCP tool surface

Initial read-only tools:

- list accessible Google Ads customers
- list PMax campaigns
- fetch PMax delivery report
- fetch search-demand insights
- validate business outcome data
- run incrementality diagnostic
- calculate contribution-margin break-even hurdle
- assess experiment readiness and estimate power
- analyze completed experiment results
- generate decision contract
- propose experiment design

There is no mutate or campaign-write tool in v1.

### LLM requirements

- Never invent spend, ROAS, revenue, savings, confidence, or test results.
- Preserve distinctions between REPORTED, OBSERVATIONAL, and EXPERIMENTAL results.
- Cite the source field or report section behind each key numeric statement.
- Ask for missing inputs instead of guessing.
- Use backend-calculated values for all arithmetic.
- Do not describe an estimated association as proof of cannibalization.

## 10. Repository topology

~~~text
pmax-auditor-suite/
├── packages/
│   ├── pmax_sentry_core/          # Open-source schemas, API client, normalization, reconciliation
│   ├── pmax_sentry_cli/           # Open-source CLI
│   ├── pmax_sentry_mcp/           # Optional read-only MCP server
│   └── pmax_sentry_pro/           # Commercial thin client for the hosted Pro API
├── apps/
│   ├── pro_api/                   # Hosted API, OAuth callbacks, report jobs
│   └── pro_web/                   # Self-service account connection and reports
├── services/
│   ├── data_ingestion/
│   ├── data_quality/
│   ├── incrementality/
│   └── decision_contracts/
├── schemas/
│   ├── delivery_report.schema.json
│   └── decision_contract.schema.json
├── docs/
└── pyproject.toml
~~~

Package names on PyPI use hyphens; Python imports use underscores. Keep the free package independently usable. The Pro package is a client for the hosted service and must not contain or imply that a license key makes shipped Python source confidential.

## 11. Dependencies

### Free

- Official google-ads Python client, pinned to a compatible API version.
- Pydantic v2 for contracts.
- Typer or Click for CLI.
- Standard library CSV and JSON output.
- Optional pandas extra for dataframe workflows.

### Pro service

- FastAPI or equivalent typed API framework.
- Pydantic v2 contracts.
- Database and job queue selected by deployment requirements.
- Statsmodels or a Bayesian library only after the specific model is validated.
- SciPy or JAX only when a supported response-curve optimizer is implemented.
- No license-verification request may include ad account metrics.

## 12. Security and privacy

- Request Google Ads access only through the documented OAuth flow or local user-managed credentials.
- Use reporting calls only in v1.
- Encrypt OAuth refresh tokens and stored account data in transit and at rest.
- Enforce tenant isolation at every API and storage boundary.
- Exclude customer IDs, search terms, revenue values, and tokens from application logs.
- Keep raw search terms local by default; make any Pro retention explicit.
- Provide account disconnect and data deletion controls.
- Record model/report version and access events without recording sensitive metric payloads.
- Define retention periods before opening the hosted beta.

## 13. Monetization and upgrade prompts

The free CLI must never turn channel mix into a waste estimate.

Acceptable free-tier prompt:

> This report shows reported PMax delivery by channel and format. Incrementality analysis needs business outcome data and a suitable measurement design.

Pro upgrade messaging may describe capabilities, but must not imply a result before the analysis has run. Do not display examples such as “42% waste” or “€18,400 saved” as if they were derived from the user’s free-tier data.

Treat one-off audit pricing and subscription pricing as hypotheses. Validate willingness to pay with paid pilots before selecting the primary model.

## 14. Delivery milestones

### Milestone 1: Reporting correctness

- Implement v26 campaign queries using channel and format segments.
- Add total-vs-segmented reconciliation and account currency/timezone handling.
- Produce CSV and JSON reports.
- Add search-demand insights as a separate, non-spend report.

### Milestone 2: Analyst usability

- Publish the free CLI and Python API.
- Document Google Cloud API access, OAuth configuration, common query errors, and data coverage semantics.
- Validate the report with multiple PMax account shapes, including accounts with paused campaigns and incomplete historical data.

### Milestone 3: Pro data intake

- Add hosted OAuth, workspace/account selection, secure token storage, and CSV business-data upload.
- Normalize business outcomes, attribution definitions, currency, and reporting timezone; accept optional promotion, price, stock, and other-media covariates.
- Add data quality status and explicit insufficient-data responses.
- Generate evidence-linked descriptive reports.

### Milestone 4: Causal measurement

- Implement one declared observational diagnostic with validation and confidence gates; do not label it causal.
- Add experiment readiness, power analysis, planning, and result ingestion for a supported design.
- Report experimental effects on the agreed business outcome, including uncertainty and conversion-lag treatment.

### Milestone 5: Marginal economics

- Calculate contribution-margin break-even hurdles from user inputs.
- Estimate a response curve only after appropriate spend-level interventions provide sufficient support.
- Keep tROAS scenarios within observed evidence and report uncertainty; do not auto-apply settings.

### Milestone 6: Agent and MCP interface

- Expose the read-only typed tools.
- Add report explanation and decision contract generation.
- Keep numeric logic in the backend and campaign changes unavailable.

## 15. Definition of done for v1

- Channel and format metrics come from supported Google Ads API segments.
- No PMax cost is derived by subtracting incompatible report totals.
- Search insight queries do not request unsupported cost metrics.
- Reports distinguish channel from format and show currency, timezone, API version, and coverage.
- A reconciliation failure is visible and cannot be silently converted into “undisclosed spend.”
- Economic reports distinguish platform-reported average ROAS, experimental iROAS, and marginal return; they disclose the outcome definition and margin basis.
- The free tier generates no waste or incrementality claim.
- Pro can return INSUFFICIENT_DATA and LOW_CONFIDENCE without fabricating values.
- Every modeled result carries its evidence class, method, assumptions, and uncertainty.
- The product does not infer a causal cannibalization coefficient, marginal curve, or optimal tROAS from residual correlation or ordinary historical spend variation.
- Experiment duration, number of treatment arms, and spend steps are selected from power and account conditions rather than fixed defaults.
- The Pro agent has no campaign-write capability in v1.
- User data can be disconnected and deleted, and sensitive values are excluded from logs.

## 16. Research grounding and interpretation

Use the literature to motivate measurement discipline and explain the economics, not to claim access to platform internals:

- [Aggarwal, Badanidiyuru, and Mehta, “Autobidding with Constraints”](https://research.google/pubs/autobidding-with-constraints/) studies optimal single-agent bidding under general affine constraints in multi-slot truthful auctions. Its assumptions matter; it does not document the deployed PMax bid equation.
- [Balseiro et al., “The Landscape of Auto-Bidding Auctions: Value Versus Utility Maximization”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3785579) compares stylized bidder objectives and seller mechanisms. Do not cite it as proof that a specific platform campaign is designed to maximize the platform’s own revenue.
- [Gordon et al., “A Comparison of Approaches to Advertising Measurement”](https://pubsonline.informs.org/doi/abs/10.1287/mksc.2018.1135) compares observational methods with 15 Facebook advertising experiments and finds that common observational approaches often fail to recover experimental effects in that setting. Use it to justify caution, not as a universal bias correction for every advertiser.
- Use the platform’s current [PMax experiment guidance](https://support.google.com/google-ads/answer/12997711?hl=en) and [GeoX implementation guidance](https://support.google.com/google-ads/answer/18073432?hl=en) for implementation constraints; recheck the guidance before shipping an experiment workflow.

Product copy may say that platform-reported value can differ from incremental advertiser profit. It must not state as fact that the platform deliberately blends inventory to transfer all advertiser surplus, that brand traffic is always non-incremental, or that a fixed target ROAS range is generally optimal. Those are hypotheses to test with account-specific evidence.
