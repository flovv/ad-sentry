# Ad Sentry — Independent Black-Box Audit Suite for AI Advertising

<p align="center">
  <a href="https://pypi.org/project/ad-sentry/"><img src="https://img.shields.io/pypi/v/ad-sentry.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/ad-sentry/"><img src="https://img.shields.io/pypi/pyversions/ad-sentry.svg" alt="Python versions"></a>
  <a href="https://github.com/flovv/ad-sentry/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
  <a href="https://developers.google.com/google-ads/api/docs/release-notes"><img src="https://img.shields.io/badge/Google%20Ads%20API-v26-green.svg" alt="Google Ads API v26"></a>
  <a href="https://polar.sh/ad-sentry"><img src="https://img.shields.io/badge/Polar.sh-Agency%20Pro%20Store-blueviolet.svg" alt="Polar Store"></a>
  <a href="https://github.com/flovv/ad-sentry/actions"><img src="https://img.shields.io/badge/tests-60%20passed%20%7C%2081%25%20coverage-brightgreen.svg" alt="Tests"></a>
</p>

**Ad Sentry** is an independent, mathematically rigorous advertising audit and delivery reconciliation engine for performance marketing teams and agencies.

Automated AI ad platforms — **Google Performance Max**, **Google Demand Gen**, and **Meta Advantage+ Shopping (ASC)** — routinely obscure channel delivery splits, bleed spend into non-converting "Zombie Products", trigger blurry auto-generated video on YouTube Shorts, suffer cross-campaign inventory collisions, and report inflated vanity ROAS driven by view-through conversion credit.

**Ad Sentry** cuts through black-box reporting to give advertisers and agencies full transparency, causal incrementality validation ($1/\mu$), and client-ready White-Label pitch decks.

---

## 🚀 The Omni-Channel Audit Trinity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AD SENTRY AUDIT MATRIX                           │
├───────────────────────┬────────────────────────────┬────────────────────────┤
│ Google PerformanceMax │ Google Demand Gen Overlap  │ Meta Advantage+ (ASC)  │
├───────────────────────┼────────────────────────────┼────────────────────────┤
│ • Channel x Format    │ • YouTube/Gmail/Discover   │ • Audience Network     │
│   reconciliation      │   inventory collision      │   placement leakage    │
│ • Asset Group Grader  │ • Engaged-View (EVC)       │ • 1-Day View vs Click  │
│   (9:16 Shorts check) │   conversion de-duplication│   Ghost-ROAS isolation │
│ • "Zombie Products"   │ • Multi-asset creative     │ • Existing customer    │
│   shopping feed audit │   fatigue detection        │   budget cap audit     │
│ • Pure search demand  │ • Cross-campaign reach     │ • Dynamic Product Ad   │
│   (zero cost fabric.) │   cannibalization          │   vs Video format split│
└───────────────────────┴────────────────────────────┴────────────────────────┘
```

---

## ⚡ Quickstart

### Installation

Install the CLI tool and core suite directly from PyPI:

```bash
pip install ad-sentry
```

*(Note: `pip install pmax-sentry` also installs this suite for backward compatibility).*

Verify your installation:

```bash
ad-audit version
# or use the pmax-audit alias:
pmax-audit version
```

---

## 📊 Core Audit Capabilities

### 1. Google Performance Max: Reconciliation, Asset Grader & Zombie Products
Audit delivery across Google Search, Display, YouTube, Discover, Gmail, and Maps while grading creative completeness and detecting non-converting shopping feed SKUs:

```bash
ad-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-31 --margin 0.40
```

Terminal output delivers 4 forensic audits in seconds:
- **Delivery Mix Reconciliation:** Segmented channel spend reconciled against total unsegmented campaign cost (Google Ads API v26).
- **Asset Group Grader (Score 0–100 / Grade A+ to F):** Audits headline depth, image ratios, and flags missing 9:16 vertical videos that trigger Google's low-quality auto-generated slideshow video on YouTube Shorts.
- **"Zombie Products" Shopping Waste:** Pinpoints products spending budget with zero conversions, calculates total cash bleed (often 15–25% of feed spend), and provides negative filter rules.
- **Economic Hurdle ($1/\mu$):** Reconciles reported ROAS against the advertiser's contribution margin break-even hurdle.

### 2. Cross-Campaign Overlap (PMax + Demand Gen)
Detect inventory collisions across YouTube in-stream, Discover feed, and Gmail between PMax and Demand Gen campaigns:

```bash
ad-audit report --customer-id 1234567890 --include-demand-gen --start-date 2026-10-01 --end-date 2026-10-31
```

### 3. Meta Advantage+ Shopping (ASC) Audit
Audit Audience Network budget leakage, isolate View-Through Ghost ROAS, and test Existing Customer Budget Cap compliance:

```bash
ad-audit meta report --account-id act_1234567890 --start-date 2026-10-01 --end-date 2026-10-31 --margin 0.40
```

### 4. Search Demand Category Insights
Categorize search term intent (Brand vs Generic) with zero fabricated spend:

```bash
ad-audit insights --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-31 -b "yourbrand"
```

---

## 💼 Agency Pro: Standalone White-Label Pitch Decks

Agencies use Ad Sentry to turn raw audit findings into beautiful, client-ready presentation pitch decks that win **\$2,000–\$10,000/month** management retainers.

Generate a standalone HTML pitch deck ready for client presentations:

```bash
ad-audit report \
  --customer-id 1234567890 \
  --margin 0.42 \
  --include-demand-gen \
  --deck client_audit_deck.html \
  --agency "Acme Growth Media" \
  --brand "Prospect Brand"
```

```bash
ad-audit meta report \
  --account-id act_1234567890 \
  --margin 0.40 \
  --deck meta_pitch_deck.html \
  --agency "Acme Growth Media" \
  --brand "Prospect Brand"
```

The resulting standalone HTML files feature:
- 🎨 **Impeccable craft styling:** High-contrast, executive dark-mode typography and responsive data cards.
- 🎯 **Asset Group Quality Grader:** Visual progress bars for asset health and YouTube Shorts risk callouts.
- 🧟 **Zombie SKU Breakdown:** Itemized table showing the exact budget wasted on non-converting products.
- 📐 **Econometric Hurdle Reconciliation:** Explicitly checks whether click ROAS clears the true contribution margin threshold ($1/\mu$).
- 🛡️ **100% Local & Privacy Compliant:** Zero client data sent to third-party cloud servers. GDPR-safe and printable to PDF via browser `Ctrl+P`.

---

## 💳 Pricing & License Tiers

Ad Sentry operates on an **Open-Core** model. The CLI, reconciliation algorithms, mock clients, and terminal/CSV/JSON reporting are 100% free and open-source under the Apache-2.0 license.

To unlock White-Label HTML pitch decks, causal experiment designs, and multi-client agency features, licenses are available via [Polar.sh](https://polar.sh/ad-sentry):

| Feature | Open-Core (Free) | Single Audit Pass | Agency Pro Retainer |
| :--- | :---: | :---: | :---: |
| **PMax Channel Reconciliation** | ✅ | ✅ | ✅ |
| **Asset Group Quality Grader** | ✅ | ✅ | ✅ |
| **"Zombie Products" Waste Detector** | ✅ | ✅ | ✅ |
| **Demand Gen Inventory Overlap** | ✅ | ✅ | ✅ |
| **Meta Advantage+ Leakage Audit** | ✅ | ✅ | ✅ |
| **Terminal, CSV, JSON Exporters** | ✅ | ✅ | ✅ |
| **FastMCP Server for AI Agents** | ✅ | ✅ | ✅ |
| **White-Label Pitch Decks (HTML)** | — | ✅ (1 Account) | ✅ (Unlimited) |
| **Client Account Capacity** | Unlimited (Local) | 1 Account | Up to 50 Accounts |
| **Causal Experiment Designer (DiD)** | — | — | ✅ |
| **Decision Contract Generator** | — | — | ✅ |
| **Price** | **Free (OSS)** | **149 € one-time** | **149 € / month** |
| **Direct Checkout** | — | [**Buy Single Pass**](https://polar.sh/ad-sentry/products/single-pass) | [**Subscribe Agency Pro**](https://polar.sh/ad-sentry/products/agency-pro) |

### Activating Your License

```bash
# Check available checkout tiers
ad-audit license buy

# Activate your key instantly
ad-audit license activate <YOUR_POLAR_KEY>

# Verify active status
ad-audit license status
```

---

## 🤖 Model Context Protocol (MCP) for AI Agents

Ad Sentry includes a native Model Context Protocol (MCP) server. Run audits directly inside **Claude Desktop**, **Cursor**, or **Antigravity**.

Launch the server:

```bash
ad-mcp
# or alias:
pmax-mcp
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

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

Add to your `.cursor/mcp.json`:

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

## 📐 Econometric Framework

Ad Sentry enforces strict evidence discipline:

1. **Break-Even Hurdle:**
   $$\text{Hurdle} = \frac{1}{\mu}$$
   where $\mu$ is the advertiser's gross contribution margin rate (e.g. at 40% margin, hurdle = 2.50x ROAS). Any campaign claiming profitability below this hurdle is losing operating margin on every sale.
2. **Ghost ROAS Isolation:**
   $$\text{Reported ROAS} = \frac{\text{Click Value} + \text{1-Day View Value}}{\text{Spend}}$$
   $$\text{True Click ROAS} = \frac{\text{Click Value}}{\text{Spend}}$$
3. **Strict Coverage Preservation:**
   Unsegmented campaign spend totals are preserved. Unmatched spend is reported as raw coverage discrepancy — never arbitrarily labeled "Display waste" or "Video".

---

## 🧪 Development & Testing

```bash
# Clone the repository
git clone https://github.com/flovv/ad-sentry.git
cd ad-sentry

# Install dependencies in editable mode
pip install -e ".[dev,all]"

# Run full test suite with coverage
pytest -v --cov
```

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
Agency Pro features and commercial distribution benefits are managed via [Polar.sh](https://polar.sh/ad-sentry).
