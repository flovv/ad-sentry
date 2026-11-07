# ad-sentry

Independent audit suite for Google Ads Performance Max, Demand Gen, and Meta Advantage+ campaigns.

[![PyPI version](https://img.shields.io/pypi/v/ad-sentry.svg)](https://pypi.org/project/ad-sentry/)
[![Python versions](https://img.shields.io/pypi/pyversions/ad-sentry.svg)](https://pypi.org/project/ad-sentry/)
[![CI](https://github.com/flovv/ad-sentry/actions/workflows/ci.yml/badge.svg)](https://github.com/flovv/ad-sentry/actions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-Interactive%20HTML%20Deck-success)](https://flovv.github.io/ad-sentry/)

Ad Sentry is a command-line audit and delivery reconciliation tool for performance marketing teams and agencies. It extracts unaggregated delivery data from Google Ads and Meta Ads to identify budget waste, attribution inflation, and structural configuration issues.

Live Demo: [https://flovv.github.io/ad-sentry/](https://flovv.github.io/ad-sentry/)

---

## Why Ad Sentry

Automated ad formats (Google Performance Max, Google Demand Gen, and Meta Advantage+ Shopping) report blended top-line ROAS that obscures underlying inventory quality. Accounts running these formats frequently experience:

1. **Unseen Display and Video Spend:** PMax blends high-intent Search and Shopping with low-intent Display Network and YouTube placements. Without channel-level decomposition, advertisers cannot see where margin is lost.
2. **Zombie Products in Shopping Feeds:** A significant portion of ad spend (typically 15% to 25% of shopping budget) is consumed by products that receive clicks but generate zero conversions over 30 to 90 day windows.
3. **Missing 9:16 Vertical Video:** When an asset group lacks a native vertical video, Google automatically generates low-resolution video slideshows for YouTube Shorts inventory, damaging brand perception and conversion rates.
4. **Demand Gen Inventory Collisions:** Running Demand Gen alongside PMax without exclusion lists causes internal bidding overlap across YouTube in-stream and Discover feeds.
5. **Attribution Over-Reporting (Meta ASC):** Meta Advantage+ Shopping blends view-through conversions into default ROAS and over-indexes on existing customers unless explicitly constrained.

Ad Sentry operates in read-only mode, queries platform APIs directly, runs offline-first, and does not transmit data to external servers.

---

## Example Output

Running a standard audit on a Performance Max campaign:

```bash
ad-audit report \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --margin 0.40
```

### 1. Channel Delivery Breakdown and Reconciliation

```text
Campaign: PMax - Core Products (ID: 9876543210)
Window:   2026-10-01 to 2026-10-31 | Currency: USD
Reported Total Cost: $1,562.82 | Attributed Value: $4,185.18 | Reported ROAS: 2.68x
Break-Even Hurdle (1 / 0.40 margin): 2.50x ROAS -> Status: CLEARS HURDLE (+0.18x margin buffer)

Channel x Format Split:
-----------------------------------------------------------------------------------------
Channel           Product Feed?  Video?      Spend   Share   Impr.  Clicks  Conv.   ROAS
-----------------------------------------------------------------------------------------
Google Search     Yes (Shopping) No        $544.15   34.8%   7,037     424   15.0  3.81x
Display Network   Yes (Dynamic)  No        $236.85   15.2%  42,910     645    7.7  1.52x
YouTube           No             Yes       $233.90   15.0%  42,520     639    7.6  1.80x
Google Search     No (Text)      No        $156.40   10.0%   1,825     111    4.0  3.23x
YouTube           Yes (Shoppable)Yes        $78.93    5.1%  12,410     186    2.5  2.43x
Gmail             Yes            No         $78.71    5.0%  12,405     186    2.5  2.22x
Discover          Yes            No         $78.27    5.0%  12,390     186    2.5  2.61x
Display Network   No             No         $78.01    5.0%  12,380     186    2.5  1.20x
Search Partners   No             No         $77.12    4.9%     992      62    2.5  2.08x
-----------------------------------------------------------------------------------------
Reconciliation: Segmented Cost ($1,562.82) == Total Cost ($1,562.82) | Discrepancy: $0.00 (100.0% coverage)
```

### 2. Asset Group Creative Health

```text
Asset Group: Clearance & Outlet Items (Ad Strength: POOR | Score: 38/100 | Grade: F)
- Headlines: 3/15 (Insufficient copy variants)
- Images: 2 (Missing 1:1 square and 4:5 portrait formats)
- 9:16 Video: MISSING (Triggers low-quality automated video on YouTube Shorts)
- Audience Signal Seed: None (Algorithm exploring without first-party customer seed)
```

### 3. Shopping Feed Zombie Product Detection

```text
Feed Analysis: 184 SKUs Audited | Total Feed Spend: $14,250.00
Zombie SKUs (0 conversions): 34 SKUs (18.5% of catalog)
Wasted Budget on Non-Converting SKUs: $2,720.00 (19.1% of feed spend)
Immediate Action: Exclude 34 Zombie SKUs via Custom Label filter to recover $2,720.00/mo.
```

---

## Quickstart

### Installation

```bash
pip install ad-sentry
```

*(Note: `pip install pmax-sentry` is maintained as a backward-compatible alias).*

Verify installation:

```bash
ad-audit version
```

### Google Ads API Configuration

Set your Google Ads credentials in a YAML file (`google-ads.yaml`) or via environment variables:

```yaml
developer_token: "INSERT_DEVELOPER_TOKEN"
client_id: "INSERT_OAUTH_CLIENT_ID"
client_secret: "INSERT_OAUTH_CLIENT_SECRET"
refresh_token: "INSERT_REFRESH_TOKEN"
use_proto_plus: true
```

If no configuration file is present, `ad-audit` automatically uses built-in realistic mock data so you can test features immediately.

---

## Commands

### 1. Performance Max Audit

```bash
ad-audit report \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --margin 0.40
```

Options:
- `--margin / -m <float>`: Advertiser gross margin rate (e.g. 0.40 for 40%) used to compute the break-even hurdle (1 / mu).
- `--include-demand-gen / -dg`: Include Demand Gen campaigns and check for cross-campaign inventory collisions.
- `--no-audit-assets`: Skip asset group creative scoring.
- `--no-audit-feed`: Skip shopping feed zombie SKU inspection.
- `--format / -f <terminal|csv|json>`: Output format (default: terminal).
- `--output / -o <path>`: Write report to a file.

### 2. Meta Advantage+ Shopping (ASC) Audit

```bash
ad-audit meta report \
  --account-id act_1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --margin 0.40
```

Audits:
- Audience Network spend leakage.
- Click-through ROAS vs 1-day view-through attribution inflation.
- Existing customer budget cap compliance.
- Dynamic Product Ad (DPA) catalog versus standalone creative split.

### 3. Search Demand Insights

```bash
ad-audit insights \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --brand "yourbrand"
```

Categorizes search term volume into Brand vs Generic without fabricating non-existent cost metrics (Google Ads API v26 does not expose cost at the search category level).

### 4. White-Label HTML Pitch Decks (Agency Pro)

Export a standalone, self-contained HTML presentation deck:

```bash
ad-audit report \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --margin 0.40 \
  --deck client_audit_deck.html \
  --agency "Acme Media" \
  --brand "Client Brand"
```

View the live sample deck: [https://flovv.github.io/ad-sentry/](https://flovv.github.io/ad-sentry/)

Features of the generated HTML deck:
- Single-file HTML with embedded SVG charts and responsive executive styling.
- Printable to PDF via browser print (Ctrl+P / Cmd+P).
- Asset group creative completeness table and zombie SKU breakdown.
- Zero external tracking scripts or client data transmission.

---

## Model Context Protocol (MCP) Server

Ad Sentry includes a built-in FastMCP server for use with Claude Desktop, Cursor, and other AI agent workflows.

Start the MCP server:

```bash
ad-mcp
```

### Claude Desktop Setup

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ad-sentry": {
      "command": "ad-mcp"
    }
  }
}
```

### Cursor Setup

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ad-sentry": {
      "command": "ad-mcp"
    }
  }
}
```

Available tools exposed via MCP:
- `list_customers`: List accessible customer accounts.
- `list_campaigns`: List PMax and Demand Gen campaigns.
- `delivery_report`: Channel and format delivery reconciliation.
- `search_insights`: Search demand classification.
- `calculate_hurdle`: Contribution margin break-even hurdle calculation.
- `propose_experiment_design`: Difference-in-Differences power analysis and design protocol.

---

## Methodology and Economics

### Break-Even ROAS Hurdle

$$\text{Hurdle} = \frac{1}{\mu}$$

Where $\mu$ is the advertiser's gross contribution margin rate. For example, at a 40% margin ($\mu = 0.40$), the minimum break-even ROAS is $1 / 0.40 = 2.50\text{x}$. Any campaign reporting ROAS below 2.50x produces a negative net profit on every attributed transaction, regardless of top-line revenue volume.

### View-Through Attribution Isolation

Meta and Google automated campaigns frequently inflate reported performance by including view-through conversions where a user saw an ad but never clicked:

$$\text{Reported ROAS} = \frac{\text{Click-Through Revenue} + \text{View-Through Revenue}}{\text{Spend}}$$

$$\text{Click ROAS} = \frac{\text{Click-Through Revenue}}{\text{Spend}}$$

Ad Sentry separates click-through conversions from view-through conversions to evaluate real commercial demand.

### Reconciliation Coverage

Platform APIs frequently present discrepancies between aggregated campaign totals and segmented dimensions. Ad Sentry computes the exact difference:

$$\text{Coverage Discrepancy} = \text{Total Campaign Cost} - \sum \text{Segmented Channel Costs}$$

If coverage discrepancy is non-zero, it is reported as an unmapped variance rather than arbitrarily attributed to Display or Video.

---

## Commercial Licensing

Ad Sentry is open-core. Core CLI tools, reconciliation algorithms, terminal reporting, and CSV/JSON exports are free under the Apache-2.0 license.

White-Label HTML deck generation and multi-client agency features require an Agency Pro subscription:

- Subscription: [Polar.sh Checkout](https://buy.polar.sh/polar_cl_vVpyPjGk5be8auvK5NLymklKYgDqjXB4iVec01V9sri)
- Activate a key:
  ```bash
  ad-audit license activate <YOUR_POLAR_KEY>
  ```
- Check license status:
  ```bash
  ad-audit license status
  ```

---

## Development

```bash
git clone https://github.com/flovv/ad-sentry.git
cd ad-sentry
pip install -e ".[dev,all]"
pytest -v
```

---

## License

Apache-2.0. Commercial agency features powered by [Polar.sh](https://buy.polar.sh/polar_cl_vVpyPjGk5be8auvK5NLymklKYgDqjXB4iVec01V9sri).
