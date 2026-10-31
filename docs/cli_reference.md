# PMax Sentry CLI Reference (`pmax-audit`)

`pmax-audit` is the open-source terminal command for Performance Max delivery observability.

## Installation

```bash
pip install pmax-sentry
# or from local repo:
pip install -e packages/pmax_sentry_core -e packages/pmax_sentry_cli
```

## Commands

### 1. View Version
```bash
pmax-audit version
```

### 2. List Eligible Campaigns
```bash
pmax-audit campaigns --customer-id 1234567890
```

### 3. Dry-Run Account Preview
```bash
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 --dry-run
```

### 4. Fetch Delivery Report (Terminal)
```bash
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30
```

### 5. Export Delivery Report (CSV / JSON)
```bash
# Export to CSV file
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 --format csv --output delivery_oct.csv

# Export to JSON file
pmax-audit report --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 --format json --output delivery_oct.json
```

### 6. Search Demand Insights
```bash
# Inspect demand categories
pmax-audit insights --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30

# With user-supplied brand dictionary
pmax-audit insights --customer-id 1234567890 --start-date 2026-10-01 --end-date 2026-10-30 --brand-term "brand" --brand-term "acme"
```
