# ad-sentry

Audit Google Performance Max, Demand Gen, and Meta Advantage+ campaigns in 30 seconds.
Find hidden budget waste, eliminate non-converting shopping SKUs, and see where your ad spend actually goes.

[![PyPI version](https://img.shields.io/pypi/v/ad-sentry.svg)](https://pypi.org/project/ad-sentry/)
[![Python versions](https://img.shields.io/pypi/pyversions/ad-sentry.svg)](https://pypi.org/project/ad-sentry/)
[![CI](https://github.com/flovv/ad-sentry/actions/workflows/ci.yml/badge.svg)](https://github.com/flovv/ad-sentry/actions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-Interactive%20Audit%20Deck-success)](https://flovv.github.io/ad-sentry/)

Interactive Demo Deck: [https://flovv.github.io/ad-sentry/](https://flovv.github.io/ad-sentry/)

---

## The Problem: What Google and Meta Hide

Automated ad formats (Google Performance Max, Google Demand Gen, and Meta Advantage+ Shopping) report a single blended ROAS in the dashboard (e.g. "3.8x ROAS"). This top-line number masks four major sources of budget waste:

1. **Hidden Display & Video Spend:** Google's UI does not show the channel split. A campaign reporting 3.8x ROAS often spends 30% to 45% of its budget on low-intent Display Network placements and YouTube videos that return under 1.2x ROAS. The campaign only looks profitable because it poached branded search queries that would have converted organically.
2. **Zombie Products in Shopping Feeds:** In most e-commerce feeds, 15% to 25% of shopping ad spend is burned on "zombie" SKUs—products that accumulate clicks over 30 to 90 days but generate zero sales.
3. **Auto-Generated YouTube Shorts Disasters:** When an asset group lacks a 9:16 vertical video, Google's system automatically generates low-quality slideshow videos with synthetic audio. These auto-generated ads run on YouTube Shorts, burn budget, and hurt conversion rates.
4. **Internal Campaign Collisions:** When PMax and Demand Gen run simultaneously without proper exclusions, they bid against each other for the same YouTube in-stream, Discover, and Gmail inventory.

Ad Sentry pulls the raw, unaggregated API data to expose these leaks in seconds. It runs locally, read-only, offline-first, and never sends account data to third-party servers.

---

## What You Get: Example Audit

Running a 30-second audit on a Performance Max campaign:

```bash
ad-audit report \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --margin 0.40
```

### 1. Unmask Hidden Channel Spend

Google's UI hides where your dollars go. Ad Sentry reconstructs the exact channel-by-format breakdown:

```text
Campaign: PMax - Core Products (ID: 9876543210)
Window:   2026-10-01 to 2026-10-31 | Currency: USD
Reported Total Cost: $1,562.82 | Attributed Value: $4,185.18 | Blended ROAS: 2.68x
Break-Even Hurdle at 40% Margin (1 / 0.40): 2.50x ROAS

Channel Breakdown:
-----------------------------------------------------------------------------------------
Channel           Inventory Type      Spend   Share   Impr.  Clicks  Conv.   ROAS
-----------------------------------------------------------------------------------------
Google Search     Shopping (Feed)   $544.15   34.8%   7,037     424   15.0  3.81x  (Profitable)
Display Network   Dynamic Remarket  $236.85   15.2%  42,910     645    7.7  1.52x  (Losing money)
YouTube           In-Stream Video   $233.90   15.0%  42,520     639    7.6  1.80x  (Losing money)
Google Search     Text Ads          $156.40   10.0%   1,825     111    4.0  3.23x  (Profitable)
YouTube           Shoppable Shorts   $78.93    5.1%  12,410     186    2.5  2.43x  (Below break-even)
Gmail             Native In-Box      $78.71    5.0%  12,405     186    2.5  2.22x  (Below break-even)
Discover          Feed Carousel      $78.27    5.0%  12,390     186    2.5  2.61x  (Marginal)
Display Network   Contextual Web     $78.01    5.0%  12,380     186    2.5  1.20x  (Losing money)
Search Partners   Partner Network    $77.12    4.9%     992      62    2.5  2.08x  (Below break-even)
-----------------------------------------------------------------------------------------
Finding: 45.3% of spend went to Display and Video inventory delivering an aggregate 1.58x ROAS.
At a 40% contribution margin, every dollar spent on these placements lost $0.37.
```

### 2. Identify Non-Converting Zombie Products

Instantly pinpoint SKUs that bleed ad spend without ever generating a conversion:

```text
Shopping Feed Analysis: 184 SKUs Audited | Total Feed Spend: $14,250.00
Zombie SKUs (Clicks with 0 Conversions): 34 SKUs (18.5% of catalog)
Wasted Spend on Zombie SKUs:             $2,720.00 (19.1% of entire shopping budget)
Immediate Recovery Opportunity:          $2,720.00 / month

Top Wasted SKUs:
- SKU-8821: Carbon Trail Running Poles (120cm) | Spend: $420.00 | Clicks: 310 | Sales: 0
- SKU-4910: Extreme Weather Winter Gaiters     | Spend: $340.00 | Clicks: 245 | Sales: 0
- SKU-2104: Ultralight Cycling Helmet (Black)   | Spend: $295.00 | Clicks: 190 | Sales: 0
- SKU-7731: Hydration Running Vest 12L Navy    | Spend: $265.00 | Clicks: 175 | Sales: 0

Action Directive: Add custom label "zombie" in Merchant Center and exclude these 34 SKUs 
to immediately reallocate $2,720/mo into top converting products.
```

### 3. Grade Asset Group Creative Completeness

Prevent Google from auto-generating low-quality creative on YouTube Shorts:

```text
Asset Group: Clearance & Outlet Items (Score: 38/100 | Grade: F)
- Headlines: 3/15 (Insufficient variants for machine learning rotation)
- Images: 2 (Missing 1:1 square and 4:5 portrait formats)
- 9:16 Vertical Video: MISSING (Google auto-generates robotic slideshow video for Shorts)
- Audience Signal Seed: MISSING (Algorithm explores cold audiences without customer data)

Action Directive: Upload native 9:16 vertical video and add first-party customer audience seed.
```

### 4. Detect Cross-Campaign Collisions (PMax vs Demand Gen)

Check if your campaigns are bidding against each other:

```text
Inventory Collision Analysis:
- YouTube In-Stream: PMax ($156.80) vs Demand Gen ($229.89) -> High Collision
- Discover Feed:     PMax ($39.58)  vs Demand Gen ($126.82) -> High Collision
- Gmail:             PMax ($38.91)  vs Demand Gen ($63.50)  -> High Collision

Action Directive: Exclude video assets from PMax to force Demand Gen to own video/discover,
or apply brand exclusion lists to prevent self-cannibalization.
```

---

## Quickstart

### Installation

```bash
pip install ad-sentry
```

*(Note: `pip install pmax-sentry` is also supported as an alias).*

Verify installation:

```bash
ad-audit version
```

### Credentials Setup

Create a `google-ads.yaml` file in your working directory or home folder:

```yaml
developer_token: "INSERT_DEVELOPER_TOKEN"
client_id: "INSERT_OAUTH_CLIENT_ID"
client_secret: "INSERT_OAUTH_CLIENT_SECRET"
refresh_token: "INSERT_REFRESH_TOKEN"
use_proto_plus: true
```

*Note: If no credentials file is present, `ad-audit` automatically uses built-in realistic mock data so you can test and explore immediately without API keys.*

---

## Core Commands

### Audit Performance Max

```bash
ad-audit report \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --margin 0.40
```

Flags:
- `--margin / -m <float>`: Contribution margin rate (e.g. 0.40 for 40%) to calculate the break-even hurdle ($1/\mu$).
- `--include-demand-gen / -dg`: Include Demand Gen campaigns to audit inventory collisions.
- `--no-audit-assets`: Skip asset group scoring.
- `--no-audit-feed`: Skip shopping feed zombie SKU inspection.
- `--format / -f <terminal|csv|json>`: Output format (default: terminal).
- `--output / -o <path>`: Save report output to disk.

### Audit Meta Advantage+ Shopping (ASC)

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
- Dynamic Product Ad (DPA) catalog versus standalone creative delivery split.

### Search Term Category Insights

```bash
ad-audit insights \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --brand "yourbrand"
```

Identifies how much search volume is coming from your brand name vs generic category terms.

### Generate Client-Ready HTML Pitch Decks

Agencies use Ad Sentry during prospective client audits to generate a standalone HTML presentation deck:

```bash
ad-audit report \
  --customer-id 1234567890 \
  --start-date 2026-10-01 \
  --end-date 2026-10-31 \
  --margin 0.40 \
  --deck client_audit_deck.html \
  --agency "Acme Performance Media" \
  --brand "Prospect Brand"
```

View an interactive sample deck: [https://flovv.github.io/ad-sentry/](https://flovv.github.io/ad-sentry/)

- Single-file standalone HTML with embedded SVG charts.
- Printable to PDF via browser (`Ctrl+P` / `Cmd+P`).
- Includes asset group creative scores, zombie SKU table, and channel split.
- 100% private and GDPR-compliant (runs locally, zero client data leaves your machine).

---

## Model Context Protocol (MCP) Server

Ad Sentry includes a built-in Model Context Protocol server. Connect it to Claude Desktop, Cursor, or Windsurf to audit ad accounts using natural language.

Start server:

```bash
ad-mcp
```

### Claude Desktop Configuration

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

### Cursor Configuration

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

---

## Commercial Licensing

Ad Sentry is open-core. All CLI tools, reconciliation logic, terminal reports, and CSV/JSON exporters are 100% free under the Apache-2.0 license.

White-Label HTML pitch decks and agency commercial rights are available via Polar.sh:

- Store: [Polar.sh Checkout](https://buy.polar.sh/polar_cl_vVpyPjGk5be8auvK5NLymklKYgDqjXB4iVec01V9sri)
- Activate a key:
  ```bash
  ad-audit license activate <YOUR_POLAR_KEY>
  ```
- Check license status:
  ```bash
  ad-audit license status
  ```

---

## License

Apache-2.0. Commercial agency features powered by [Polar.sh](https://buy.polar.sh/polar_cl_vVpyPjGk5be8auvK5NLymklKYgDqjXB4iVec01V9sri).
