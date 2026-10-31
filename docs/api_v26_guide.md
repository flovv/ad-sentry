# Google Ads API v26 Integration Guide

## Pinned API Version

PMax Sentry pins its integration to Google Ads API version **v26**. Every generated delivery report, export, and MCP tool output includes the explicit API version attribute.

## Query Shapes & Resources

### 1. Segmented Delivery Query

PMax Sentry queries the `campaign` resource with channel and format segments:

```sql
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
  AND segments.date BETWEEN '{start_date}' AND '{end_date}'
```

### 2. Unsegmented Campaign Total Query

To verify reporting coverage and detect segmentation loss, an unsegmented campaign query is executed separately across the identical date window:

```sql
SELECT
  campaign.id,
  campaign.name,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM campaign
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
  AND segments.date BETWEEN '{start_date}' AND '{end_date}'
```

The unsegmented cost is then compared against the sum of the segmented rows to produce the reconciliation audit.

### 3. Search Demand Insights Query

Search term category insights are fetched from the `campaign_search_term_insight` resource:

```sql
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
  AND segments.date BETWEEN '{start_date}' AND '{end_date}'
```

> [!IMPORTANT]
> The search insight query **never requests `metrics.cost_micros`**.
> Google Ads search insight data is a categorized demand indicator and does not provide spend. PMax Sentry strictly prohibits subtracting search categories to derive brand/generic spend.
