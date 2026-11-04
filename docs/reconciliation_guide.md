# Delivery Reconciliation & Coverage Audit Guide

## Principles

1. **Dual Query Comparison:**
   Every PMax audit fetches two independent views across the identical customer ID, date window, and API version:
   - The unsegmented campaign cost total: $C_{\text{unsegmented}}$
   - The segmented channel $\times$ format cost records: $\sum C_{\text{segmented}}$

2. **Raw Difference Preservation:**
   $$\text{difference\_micros} = C_{\text{unsegmented}} - \sum C_{\text{segmented}}$$
   - Never masked with $\max(0, \text{difference})$.
   - If $\sum C_{\text{segmented}} > C_{\text{unsegmented}}$, a negative raw difference is explicitly reported.

3. **Strict Non-Attribution of Discrepancies:**
   - Unexplained discrepancies are **never** labeled "Display", "Video", or "waste".
   - Discrepancies reflect API segmentation boundaries, processing delays, or unsupported network flags, not unobserved platform malice.

## Coverage Status Definitions

| Status | Condition | Description |
|---|---|---|
| `COMPLETE` | $|\text{ratio} - 1.0| \le 0.001$ | Segmented spend reconciles with campaign total within 0.1% tolerance. |
| `PARTIAL` | $|\text{ratio} - 1.0| > 0.001$ | Segmented query under-reports or over-reports spend relative to totals. Raw difference and ratio are preserved. |
| `UNAVAILABLE` | $\sum C_{\text{segmented}} = 0$ and $C_{\text{unsegmented}} > 0$ | PMax segmentation data was not returned by the API for the window. |

## Terminal & Export Appearance

Every CSV and JSON export includes the `coverage` block with:
- `status`: `COMPLETE`, `PARTIAL`, or `UNAVAILABLE`
- `segmented_cost_micros`: integer micros
- `unsegmented_cost_micros`: integer micros
- `difference_micros`: raw signed difference
- `coverage_ratio`: exact Decimal ratio
- `reasons`: diagnostic list detailing observed boundaries
