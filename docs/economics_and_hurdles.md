# Contribution Economics & Break-Even Hurdles

## Mathematical Formulation

Let $\mu \in (0, 1]$ represent the advertiser's contribution-margin rate before ad spend, accounting for all variable costs (COGS, fulfillment, payment fees, returns):

$$\text{Incremental Net Profit} = (\text{Incremental Revenue} \cdot \mu) - \text{Incremental Ad Spend}$$

Setting $\text{Incremental Net Profit} = 0$:

$$(\text{Incremental Revenue} \cdot \mu) = \text{Incremental Ad Spend}$$
$$\frac{\text{Incremental Revenue}}{\text{Incremental Ad Spend}} = \frac{1}{\mu}$$

$$\text{Break-Even iROAS} = \frac{1}{\mu}$$

### Example
If an advertiser operates at a 25% contribution margin ($\mu = 0.25$):
$$\text{Break-Even iROAS} = \frac{1}{0.25} = 4.00\text{x}$$
Every incremental media dollar spent on PMax must yield at least \$4.00 of incremental business revenue to prevent margin erosion.

## Marginal Returns vs. Average ROAS

- **Average ROAS** reports total value divided by total spend across all historical impressions. It does *not* indicate whether the last dollar spent was profitable.
- **Profit-Maximizing Spend** occurs where **marginal incremental ROAS** equals the hurdle $\frac{1}{\mu}$:
  $$\text{Marginal iROAS} = \frac{\partial \text{Incremental Revenue}}{\partial \text{Ad Spend}} = \frac{1}{\mu}$$
- Estimating a true marginal response curve requires multiple spend intervention levels in an experiment; ordinary historical spend variation is confounded and cannot establish an optimal target ROAS floor.
