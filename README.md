# PMax Sentry — Delivery Observability & Incrementality Audit Suite

<p align="center">
  <a href="https://pypi.org/project/pmax-sentry/"><img src="https://img.shields.io/pypi/v/pmax-sentry.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/pmax-sentry/"><img src="https://img.shields.io/pypi/pyversions/pmax-sentry.svg" alt="Python versions"></a>
  <a href="https://github.com/flovv/pmax-sentry/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
  <a href="https://developers.google.com/google-ads/api/docs/release-notes"><img src="https://img.shields.io/badge/Google%20Ads%20API-v26-green.svg" alt="Google Ads API v26"></a>
  <a href="https://polar.sh/pmax-sentry"><img src="https://img.shields.io/badge/Polar.sh-Agency%20Pro%20Store-blueviolet.svg" alt="Polar Store"></a>
  <a href="https://github.com/flovv/pmax-sentry/actions"><img src="https://img.shields.io/badge/tests-55%20passed%20%7C%2081%25%20coverage-brightgreen.svg" alt="Tests"></a>
</p>

**PMax Sentry** is an independent, mathematically rigorous advertising audit and delivery reconciliation engine for performance marketing teams and agencies.

Automated AI campaigns — **Google Performance Max**, **Google Demand Gen**, and **Meta Advantage+ Shopping (ASC)** — routinely obscure channel delivery splits, suffer silent cross-campaign inventory collisions, and report inflated vanity ROAS driven by view-through conversion credit.

**PMax Sentry** cuts through black-box reporting to give advertisers and agencies full transparency, causal incrementality validation, and client-ready White-Label pitch decks.

---

## 🚀 The Audit Trinity

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PMAX SENTRY AUDIT TRINITY                       │
├───────────────────────┬────────────────────────────┬────────────────────────┤
│ Google PerformanceMax │ Google Demand Gen Overlap  │ Meta Advantage+ (ASC)  │
├───────────────────────┼────────────────────────────┼────────────────────────┤
│ • Channel x Format    │ • YouTube/Gmail/Discover   │ • Audience Network     │
│   reconciliation      │   inventory collision      │   placement leakage    │
│ • Unsegmented spend   │ • Engaged-View (EVC)       │ • 1-Day View vs Click  │
│   gap preservation    │   conversion de-duplication│   Ghost-ROAS isolation │
│ • Pure search demand  │ • Multi-asset creative     │ • Existing customer    │
│   (zero cost fabric.) │   fatigue detection        │   budget cap audit     │
└───────────────────────┴────────────────────────────┴────────────────────────┘
```

---

## ⚡ Quickstart

### Installation

Install the CLI tool and core suite directly from PyPI:

```bash
pip install pmax-sentry
```

Or install with Google Ads API live connector:

```bash
pip install "pmax-sentry[all]"
```

Verify your installation:

```bash
pmax-audit version
```

---

## 📊 Core Audit Commands

### 1. Google Performance Max Delivery Audit
Fetch reported delivery mix, reconcile segmented metrics against total unsegmented campaign cost, and calculate the break-even hurdle ($1/\mu$):

```bash
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-31 --margin 0.40
```

### 2. Cross-Campaign Overlap (PMax + Demand Gen)
Detect inventory collisions across YouTube in-stream, Discover feed, and Gmail between PMax and Demand Gen campaigns:

```bash
pmax-audit report --customer-id 1234567890 --include-demand-gen --start-date 2026-10-01 --end-date 2026-10-31
```

### 3. Meta Advantage+ Shopping (ASC) Audit
Audit Audience Network budget leakage, isolate View-Through ROAS inflation, and test Existing Customer Budget Cap compliance:

```bash
pmax-audit meta report --account-id act_1234567890 --start-date 2026-10-01 --end-date 2026-10-31 --margin 0.40
```

### 4. Search Demand Category Insights
Categorize search term intent (Brand vs Generic) with zero fabricated cost:

```bash
pmax-audit insights --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-31 -b "yourbrand"
```

---

## 💼 Agency Pro: Standalone White-Label Pitch Decks

Agencies use PMax Sentry to turn raw audit findings into beautiful, client-ready presentation pitch decks that win **\$2,000–\$10,000/month** management retainers.

Generate a standalone HTML pitch deck ready for client presentations:

```bash
pmax-audit report \
  --customer-id 1234567890 \
  --margin 0.42 \
  --include-demand-gen \
  --deck client_audit_deck.html \
  --agency "Acme Growth Media" \
  --brand "Prospect Brand"
```

```bash
pmax-audit meta report \
  --account-id act_1234567890 \
  --margin 0.40 \
  --deck meta_pitch_deck.html \
  --agency "Acme Growth Media" \
  --brand "Prospect Brand"
```

The resulting standalone HTML files feature:
- 🎨 **Impeccable craft styling:** High-contrast, executive-ready dark-mode typography and responsive data cards.
- 📐 **Econometric Hurdle Reconciliation:** Explicitly checks whether click ROAS clears the true contribution margin threshold ($1/\mu$).
- 🛡️ **Zero third-party trackers:** Completely self-contained, printable to PDF via browser `Ctrl+P`.

---

## 💳 Pricing & License Tiers

PMax Sentry operates on an **Open-Core** model. The CLI, reconciliation algorithms, mock clients, and terminal/CSV/JSON reporting are 100% free and open-source under the Apache-2.0 license.

To unlock White-Label HTML pitch decks, causal experiment designs, and multi-client agency features, licenses are available via [Polar.sh](https://polar.sh/pmax-sentry):

| Feature | Open-Core (Free) | Single Audit Pass | Agency Pro Retainer |
| :--- | :---: | :---: | :---: |
| **PMax Channel Reconciliation** | ✅ | ✅ | ✅ |
| **Demand Gen Inventory Overlap** | ✅ | ✅ | ✅ |
| **Meta Advantage+ Leakage Audit** | ✅ | ✅ | ✅ |
| **Terminal, CSV, JSON Exporters** | ✅ | ✅ | ✅ |
| **FastMCP Server for AI Agents** | ✅ | ✅ | ✅ |
| **White-Label Pitch Decks (HTML)** | — | ✅ (1 Account) | ✅ (Unlimited) |
| **Client Account Capacity** | Unlimited (Local) | 1 Account | Up to 50 Accounts |
| **Causal Experiment Designer (DiD)** | — | — | ✅ |
| **Decision Contract Generator** | — | — | ✅ |
| **Price** | **Free (OSS)** | **149 € one-time** | **149 € / month** |
| **Direct Checkout** | — | [**Buy Single Pass**](https://polar.sh/pmax-sentry/products/single-pass) | [**Subscribe Agency Pro**](https://polar.sh/pmax-sentry/products/agency-pro) |

### Activating Your License

```bash
# Check available checkout tiers
pmax-audit license buy

# Activate your key instantly
pmax-audit license activate <YOUR_POLAR_KEY>

# Verify active status
pmax-audit license status
```

---

## 🤖 Model Context Protocol (MCP) for AI Agents

PMax Sentry includes a native Model Context Protocol (MCP) server. Run audits directly inside **Claude Desktop**, **Cursor**, or **Antigravity**.

Launch the server:

```bash
pmax-mcp
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pmax-sentry": {
      "command": "pmax-mcp"
    }
  }
}
```

### Cursor Configuration

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pmax-sentry": {
      "command": "pmax-mcp"
    }
  }
}
```

---

## 📐 Econometric Framework

PMax Sentry enforces strict evidence discipline:

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
git clone https://github.com/flovv/pmax-sentry.git
cd pmax-sentry

# Install dependencies in editable mode
pip install -e ".[dev,all]"

# Run full test suite with coverage
pytest -v --cov
```

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
Agency Pro features and commercial distribution benefits are managed via [Polar.sh](https://polar.sh/pmax-sentry).
