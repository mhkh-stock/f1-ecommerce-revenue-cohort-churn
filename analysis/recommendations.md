# Flagship 1 — 3 recommendations (Phase D, 9 Nov 2026)

Every number below is verified: Phase A leak notes (`sql/03`–`sql/08`),
Phase B cohort LTV (`sql/09`, re-checked three ways in
`src/check_ltv_recheck.py`, 13 checks), Phase C RFM + churn
(`sql/10`–`sql/11`, `src/check_rfm.py`, 30 checks), and the Phase D
validation (`sql/12`, `src/validate_headlines.py`, 11 headlines
reconciled three ways). Revenue = SUM(price) only; freight is delivery
cost, never revenue. Customers counted by `customer_unique_id`.

The logic that orders them: LTV is flat (BRL 131–167 across every
cohort with >300 customers; overall BRL 142.44) and retention is
near zero (96.9% one-time buyers; 98.71–99.23% churn in the
fully-observed 2016–2017 cohorts). So the business cannot grow by
keeping customers better — it grows by making each order cheaper to
serve, by finding customers in new places, and by spending retention
money only where a second order is plausible.

## Recommendation 1 — Fix freight pricing on electronics first

**The evidence.** Freight is 16.6% of item price overall
(BRL 2,256,599.44 on BRL 13,591,643.70 of revenue), and 4,119 items
(3.7%) cost more to deliver than they sell for — BRL 100,273.81 of
freight against BRL 72,613.86 of price. But the leak is concentrated,
not general (`sql/08`): electronics (`eletronicos`) runs freight at
29.07% of price, and 611 of its 2,767 items (22.08%) cost more to
deliver than they sell for — more than double the next-worst large
category (`telefonia`, 9.46%). The biggest freight bills sit elsewhere
(`cama_mesa_banho` BRL 204,693.04) only because those categories sell
more, not because their rates are worse.

**The move.** Price delivery by category, starting with electronics:
a minimum order value or a delivery surcharge on low-price electronics
items, and a free-delivery threshold that pulls the small electronics
basket above the freight-cost line. Do not apply a blanket freight
surcharge — `relogios_presentes` (watches/gifts) proves the point:
BRL 1,205,005.68 of revenue at 8.34% freight, 0.53% over-100% items.

**What success looks like.** The over-100% item count for electronics
falls from 611 toward the `telefonia` rate (~9%), and the overall
freight share moves from 16.6% toward ~14% — worth roughly
BRL 350,000 across a dataset this size, without touching a single
price a customer sees on the product page.

**Follow-up (not assumed):** whether electronics' freight problem is
weight-driven — join `dim_product.product_weight_g` next; if heavy
items drive it, the fix is a weight-based delivery band, not a
category surcharge.

## Recommendation 2 — Grow acquisition outside São Paulo

**The evidence.** São Paulo alone is BRL 5,202,955.05 — 38.28% of
revenue from 39,981 customers — and the top 3 states (SP + RJ + MG)
are 63.36% of revenue. A São Paulo disruption is a revenue
disruption, and the LTV re-check says a customer acquired anywhere
is worth about the same (BRL 131–167 per cohort) — so there is no
evidence that SP customers are better customers, only that there are
more of them.

**The move.** Shift marginal acquisition spend to the next states
(RJ and MG first, then the rest of the top 10), and measure cost per
acquired customer by state before scaling — the LTV flatness means
the test to run is "which state acquires cheapest", not "which state
buys most".

**What success looks like.** SP's revenue share falls below 35%
while total revenue grows — diversification that costs nothing in
customer quality, because quality does not vary by cohort in this
data.

## Recommendation 3 — Retain the 617 at-risk repeat buyers only; stop broad win-back

**The evidence.** Churn is 70.01% (66,802 of 95,420 customers) and
the at-risk group (last purchase 3–6 months ago) is 18,594 customers
with BRL 2,751,210.98 attached. But only 617 of them are repeat
buyers — worth BRL 169,495.02. The other 17,977 are one-time buyers
whose single purchase was 3–6 months ago, and one-time buyers return
at ~0.5%. The top-25 at-risk list is all one-time buyers. Champions
is 128 people (0.13%, BRL 58,712.47) and all five repeat-buyer
segments together are 2,913 customers (3.05%).

**The move.** Any retention spend — win-back offers, re-engagement
emails, loyalty perks — targets the 617 at-risk repeat buyers and
nobody else. No loyalty programme for the 92,507 one-time buyers:
there is no second purchase to programme for. And the dashboard must
report "revenue at risk" as **BRL 169,495.02**, not BRL 2.75M — the
bigger number is one-time revenue that was never going to repeat,
and showing it as at-risk would mislead whoever reads it.

**What success looks like.** A win-back campaign to 617 people with
a measured second-purchase rate — even a 10% save rate is 62
customers and ~BRL 17,000 of repeat revenue, against a campaign that
costs almost nothing to target. A campaign to 18,594 people at the
same offer would spend ~30× as much to reach the same 617.

## What these three do not cover

- **Order-status restatement (still open).** Headline revenue as
  loaded includes ~1.24% of orders that are cancelled or unavailable
  (625 + 609 of 99,441). The restatement is the next Phase D block;
  until it lands, every number above carries that caveat, and the
  recommendations are sized on the loaded figures.
- **The Nov 2016 gap and the clean 2017–2018 trend** — still open
  from the Phase A leak notes; they shape the growth story in the
  executive summary, not these three moves.
- **No recommendation spends on acquisition volume alone.** With LTV
  flat, buying more of the same customers at the same cost does not
  change the business — the first two recommendations change the
  economics of each order and the geography of the next customer
  instead.

## Phase D status after this step

LTV re-check DONE (this run: `sql/13_cohort_ltv_recheck.sql` +
`src/check_ltv_recheck.py`, 13 checks, 0 failures) · 3 recommendations
DONE (this file) · executive summary skeleton DONE
(`analysis/executive_summary_skeleton.md`). Remaining Phase D: the
order-status restatement + the Nov 2016 gap check + the clean
2017–2018 trend, then Phase E (Power BI dashboard, 14–20 Nov).
