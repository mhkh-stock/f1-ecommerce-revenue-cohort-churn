# Flagship 1 — One-pager (Phase F, 21 Nov 2026 — restated-basis final pass)

**Olist E-commerce Revenue, Cohort & Churn** · Brazilian marketplace,
Sep 2016 – Aug 2018 · Real Olist data, 112,650 order items

> **One sentence:** Olist earned **BRL 13,494,400.74** from **94,983
> customers** across **98,199 orders**, but it buys customers it does
> not keep — **97.0% buy once**, lifetime value is flat at about
> **BRL 142** per customer, and **69.99% have churned** — so the
> margin is in freight and geography, not in loyalty.

## The numbers

| KPI | Value |
|---|---:|
| Revenue (restated, excl. cancelled + unavailable) | BRL 13,494,400.74 |
| Orders / customers (restated) | 98,199 / 94,983 |
| Average order value (restated) | BRL 137.42 |
| Freight — delivery cost (restated) | BRL 2,245,816.19 · 16.64% of price |
| Items costing more to deliver than they sell for | 4,100 (3.6%) |
| One-time buyers | 92,096 of 94,983 (97.0%) |
| Lifetime value per customer | BRL 142.07 (BRL 131–163 by cohort) |
| Churned / active | 66,476 (69.99%) / 28,507 (30.01%) |
| Saveable at-risk revenue | BRL 168,541.14 (611 repeat buyers) |
| São Paulo share of revenue | 38.27% (top 3 states 63.35%) |
| Peak month | Nov 2017 — BRL 1,003,862.14, 7,421 orders |
| Growth | Aug 2018 YoY +49.38% — decelerating through 2018 |

## The three findings

1. **Revenue is real but leaky.** Freight eats 16.64% of every real
   of price. The leak is concentrated in electronics — 29.50% freight
   (restated), 22.18% of its items cost more to deliver than they sell
   for — not spread across the catalogue, which is why it is fixable
   without touching product prices.
2. **Customers are bought, not kept.** Lifetime value sits in a narrow
   BRL 131–163 band for every cohort with more than 300 customers,
   including the Nov 2017 Black Friday cohort (7,188 customers,
   BRL 140.30 each). Month-1 retention is 0.56% for that cohort and
   0.71% for its neighbour: the discount-buyer hypothesis fails
   because nothing retains.
3. **Growth is volume, not basket size — and it is slowing.** Orders
   grew about 8–9x from Jan 2017 (787) to a typical 2018 month
   (6,145–7,187 orders); average order value did not grow at all.
   Year-on-year growth decelerates across 2018 (+242% in Feb to +49%
   in Aug). The peak month and the retention problem are the same
   event: the Black Friday cohort bought once and never came back.

## The three moves

1. **Fix freight pricing on electronics first** — category-level
   delivery pricing (minimum order value / surcharge on low-price
   electronics). Worth roughly BRL 350,000 across a dataset this
   size; freight share from 16.6% toward ~14%.
2. **Grow acquisition outside São Paulo** — shift marginal spend to
   RJ and MG first; LTV is flat everywhere, so the test is which
   state acquires cheapest. Target: SP share below 35% while total
   revenue grows.
3. **Retain the 611 at-risk repeat buyers only** — win-back offers to
   those 611 people (BRL 168,541.14). Never a broad campaign to all
   18,536 at-risk customers: the bigger number (BRL 2.73M) is
   one-time revenue that was never going to repeat.

## Read this before quoting any number

- **Restated headline.** The headline revenue excludes cancelled and
  unavailable orders. As loaded (all statuses) it is
  BRL 13,591,643.70 — the restatement is only −0.72%.
- **Data window.** The clean trend runs Jan 2017 → Aug 2018. Nov 2016
  has zero orders in the source and Sep 2018 is a 1-order stub
  (16 raw orders, 15 cancelled, BRL 145.00) — neither is plotted as
  a trend point.
- **Two unrelated 611s.** Electronics items costing more to deliver
  than they sell for = 611 items. At-risk repeat buyers = 611 people.
  Same number, different things — never mix them.
- **Power BI status.** The dashboard model, 12 DAX measures and page
  layouts are built and verified (`powerbi/`); the `.pbix` itself is
  NOT YET BUILT — it needs Power BI Desktop on a Windows machine.
  The published-report link slot in the README stays empty until then.
- **Sources.** Every figure is verified in `sql/03`–`sql/16` and
  `src/check_*.py` (full regression sweep 21 Nov 2026). All figures
  restated (excl. cancelled + unavailable) unless labelled
  all-status. Revenue = SUM(price) only; freight is delivery cost,
  never revenue. Customers counted by `customer_unique_id`.
