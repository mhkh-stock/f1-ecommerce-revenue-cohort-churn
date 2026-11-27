# Flagship 1 — Revenue leak notes (Phase A draft, 4 Nov 2026)

Draft findings from `sql/03`–`sql/07`, all run against the real loaded
star schema (`data/processed/f1.db`, 112,650 fact rows). Every query's
revenue total reconciles to the ingest record: **BRL 13,591,643.70**.
Freight total reconciles separately: **BRL 2,256,599.44**.

## Headline findings (draft — Phase D re-validates each one)

1. **Freight is the clearest leak.** Overall freight = 16.6% of item
   price. 4,119 items (3.7%) cost MORE to deliver than they sell for
   (freight BRL 100,273.81 against price BRL 72,613.86), and a further
   14,878 items sit in the 50–100% freight band. Together, high +
   over-100% freight items are 18,997 items (16.9%) carrying only
   BRL 574,501.78 of revenue against BRL 427,053.62 of freight.
2. **Revenue is geographically concentrated.** São Paulo (SP) alone
   is BRL 5,202,955.05 — 38.28% of revenue from 39,981 customers.
   Top 3 states (SP + RJ + MG) = 63.36%. A São Paulo disruption is a
   revenue disruption; growth outside SP is the diversification story.
3. **No single category dominates.** Top category beleza_saude is
   only 9.26% (BRL 1,258,681.34); the top 5 together are 36.14%.
   This is a broad-catalogue business, not a one-category business —
   category strategy is about the long tail, not one winner.
4. **It is a low-ticket business with a high-ticket tail.** Median
   item price is BRL 74.99; 64.06% of items sell under BRL 100 but
   carry only 27.23% of revenue, while the 2.88% of items priced
   BRL 500+ carry 22.03% of revenue. Low-ticket volume + freight is
   where margin leaks; high-ticket items are where revenue sits.
5. **Early months are a trickle, not a launch.** Sep 2016 has 3
   orders, Oct 2016 has 308, Nov 2016 has NO fact rows at all, Dec
   2016 has 1 order. Month-on-month growth figures before 2017 are
   meaningless (e.g. +1,103,687.8% into Jan 2017) and must never be
   quoted; the trend story starts in 2017.

## Order-status decision (the PLAN.md gap, decided 4 Nov 2026)

The raw orders file (`data/raw/olist_orders_dataset.csv`) DOES carry
`order_status`, but the star schema does not — so this draft reports
revenue on fact rows as loaded, including every status. The raw
counts bound the error: cancelled 625 orders (0.63%) and unavailable
609 (0.61%) of 99,441 orders — together ~1.24% of orders. That is
small, but it is not zero, and cancelled orders should not count as
revenue. **Decision:** Phase D adds an `order_status` dimension (or a
filtered fact view) and restates headline revenue excluding
cancelled/unavailable orders, with the size of the restatement shown
explicitly. Until then, every Phase A number carries this caveat:
revenue as loaded, ~1.2% of orders potentially non-revenue.

## What Phase D must re-check before these become final

- Restated revenue after the order-status filter, and the exact delta.
- Whether high-freight items cluster in specific categories or states
  (freight × category cross-tab) — the leak may be a logistics story
  for a few categories, not a general one.
- Whether the Nov 2016 gap is a data gap or a real zero month
  (check the raw orders file for Nov 2016 purchase timestamps).
- The 2017–2018 monthly trend once the trickle months are excluded,
  for a clean growth story.
