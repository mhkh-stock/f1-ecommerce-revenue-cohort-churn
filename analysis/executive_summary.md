# Flagship 1 — Executive summary (FINAL, Phase F final pass, 21 Nov 2026)

Two-page executive summary for the Olist e-commerce revenue, cohort
and churn analysis. FINAL for publish (Fri 27 Nov 2026). **All figures
are restated (excluding cancelled + unavailable orders) unless labelled
all-status.** Every figure below is verified — Phase A leak notes
(`sql/03`–`sql/08`), Phase B cohort LTV (`sql/09`, re-checked in
`sql/13`), Phase C RFM + churn (`sql/10`–`sql/11`), Phase D validation
(`sql/12`), order-status restatement (`sql/14`, 36 checks) and clean
trend (`sql/16`, 25 checks), plus the Phase E Power BI model
(`powerbi/verified_measures.json`) and page checks. The 13 Nov draft
carried several all-status figures in a restated summary; the final
pass recomputed each one from the model DB
(`src/check_executive_summary.py`) and replaced it with its restated
value — the full old→new list is in `docs/publish_checklist.md` §6.
Revenue = SUM(price) only; freight is delivery cost, never
revenue. Customers counted by `customer_unique_id`.

## Headline (one sentence)

Olist's Brazilian e-commerce business earned **BRL 13,494,400.74**
from **94,983 customers** across **98,199 orders** (Sep 2016 –
Aug 2018), but it buys customers it does not keep: **97.0% buy
once**, lifetime value is flat at about **BRL 142** per customer,
and **69.99% have churned** — so the margin is in freight and
geography, not in loyalty.

## The numbers that carry the story

| Number | Value | Source |
|---|---:|---:|
| Revenue (restated, excl. cancelled + unavailable) | BRL 13,494,400.74 | `sql/14` |
| Revenue as loaded (all statuses, reconciliation footnote) | BRL 13,591,643.70 | `sql/12` |
| Orders / customers (restated) | 98,199 / 94,983 | `sql/14` |
| Freight (delivery cost, restated) | BRL 2,245,816.19 — 16.6% of price | `sql/14` |
| Items costing more to deliver than they sell for | 4,100 (3.6%) | `sql/14`, `verified_measures.json` |
| One-time buyers | 92,096 of 94,983 (97.0%) | `sql/14` |
| Lifetime value per customer | BRL 142.07 (range BRL 131–163 by cohort) | model DB, 20 cohorts Jan 2017–Aug 2018 |
| Churned / active | 66,476 (69.99%) / 28,507 (30.01%) | `sql/14` |
| Saveable at-risk revenue | BRL 168,541.14 (611 repeat buyers) | `sql/14` |
| São Paulo share of revenue | 38.27% (top 3 states 63.35%) | `verified_measures.json`, model DB |
| Peak month | Nov 2017 — BRL 1,003,862.14, 7,421 orders | `sql/16` |
| Current growth rate | Aug 2018 YoY +49.38% (decelerating) | `sql/16` |

## The story in three paragraphs

1. *Revenue is real but leaky.* Freight eats 16.6% of every real
   of price, and 4,100 items cost more to deliver than they sell
   for. The leak is concentrated in electronics (29.50% freight,
   22.18% of its items over 100%), not spread across the catalogue
   — which is why it is fixable without touching product prices.
   The restatement behind the headline is small but honest:
   cancelled and unavailable orders carried only BRL 97,242.96
   (0.72%) of the loaded revenue, so the restated figure is the
   revenue the business actually earned.
2. *Customers are bought, not kept.* Lifetime value sits in a
   narrow BRL 131–163 band for every cohort with more than 300
   customers, including the Nov 2017 Black Friday cohort (7,188
   customers, BRL 140.30 each) — size bought revenue, not better
   customers. Retention in month 1 is 0.56% for that cohort and
   0.71% for its neighbour: the discount-buyer hypothesis fails
   because nothing retains. In the fully-observed 2016–2017
   cohorts, 98.62–99.24% of customers have churned.
3. *Growth is volume, not basket size — and it is slowing.*
   Revenue rose from BRL 120,098 in Jan 2017 to a BRL 838k–994k
   monthly band through 2018, but no month beats Nov 2017's
   BRL 1,003,862. Orders grew about 8–9x from Jan 2017 (787) to a
   typical 2018 month (6,145–7,187 orders); average order value did
   not grow at all (BRL 152.60 in Jan 2017, a BRL 126–145 band in
   2018). Year-on-year growth decelerates across 2018 (+242% in Feb
   to +49% in Aug). The peak month and the retention problem are the
   same event: the Black Friday cohort bought once and never came
   back. Geography is the concentration risk on top: São Paulo is
   38.27% of revenue and the top 3 states are 63.35%, while no
   single category dominates (top category 9.31%) — diversified
   by product, concentrated by place.

[Visual 1 — Phase F: clean monthly trend Jan 2017 → Aug 2018,
restated revenue, with the 2016 and Sep 2018 stubs labelled, never
plotted as trend points.]

[Visual 2 — Phase F: cohort retention heatmap, month 0–11, showing
the near-zero month-1 retention across all cohorts.]

## The three moves

1. **Fix freight pricing on electronics first.** Category-level
   delivery pricing — a minimum order value or delivery surcharge
   on low-price electronics items, and a free-delivery threshold
   that pulls the small electronics basket above the freight-cost
   line. Success = electronics over-100% rate from 22.18% toward
   ~9%, overall freight share from 16.6% toward ~14% — worth
   roughly BRL 350,000 across a dataset this size (restated basis:
   2.64 points of BRL 13,494,400.74 ≈ BRL 356,000), without
   touching a single product price. (Full text:
   `analysis/recommendations.md` — note its evidence paragraph
   quotes the all-status figures; the moves are unchanged.)
2. **Grow acquisition outside São Paulo.** Shift marginal
   acquisition spend to RJ and MG first, then the rest of the top
   10, and measure cost per acquired customer by state before
   scaling — LTV is flat everywhere, so the test is "which state
   acquires cheapest", not "which state buys most". Success = SP
   share below 35% while total revenue grows.
3. **Retain the 611 at-risk repeat buyers only.** Win-back offers
   to those 611 people, worth BRL 168,541.14 — never a broad
   campaign to all 18,536 at-risk customers. Report "revenue at
   risk" as BRL 168,541.14, not BRL 2.73M: the bigger number is
   one-time revenue that was never going to repeat. Even a 10%
   save rate is ~61 customers and ~BRL 17,000 of repeat revenue,
   against a campaign that costs almost nothing to target.

## Caveats the summary carries (not footnotes)

- All figures are restated (excl. cancelled + unavailable) unless
  labelled all-status. Revenue as loaded includes
  cancelled/unavailable orders; the headline above excludes them
  (BRL 13,494,400.74) and the all-status figure
  (BRL 13,591,643.70) is quoted once, as a reconciliation footnote,
  so a reader who re-adds the raw files lands on the same total.
  Delivered-only (BRL 13,221,498.11) is NOT used: only
  BRL 97,242.96 of its gap is genuinely non-revenue; the rest is
  1,721 in-flight orders.
- Churn is 59.50–69.99% depending on the cut-off (2018-09-03 vs
  2018-10-17); 69.99% is the headline under the locked
  definition, and the 44 dead days after the last item-bearing
  purchase (2018-09-03) put a +44-day floor under every recency.
- 2018 cohorts read worse on repeat share only because they had
  less calendar time to make a second purchase (censoring, not a
  worsening business); the honest comparison set is cohorts up
  to Dec 2017.
- RFM segments describe *when* people bought once, not a loyalty
  ladder — the frequency score is meaningless here (92,096
  customers share frequency = 1), so segments use R score +
  actual order count.
- The trend line is Jan 2017 → Aug 2018. November 2016 holds zero
  orders in the source and September 2018 holds one order with
  items (BRL 145.00) — the extract ends Aug 2018. Never quote Jan
  2018's +687.24% YoY on its own (it is against a 787-order
  January); quote Aug 2018's +49.38% as the current growth rate,
  and H1 2018 vs H1 2017 (+177.88%) only with the base-effect
  warning.
- Two figures that happen to share the number 611 are unrelated:
  611 electronics items (of 2,755) cost more to deliver than they
  sell for, and 611 at-risk repeat buyers are worth saving. Both
  counts are 611 under the restated basis too — verified, not
  assumed. Do not mix them.

## Phase F final pass (21 Nov 2026) — what changed from the draft

- Every figure recomputed from the model DB on the restated basis
  (`src/check_executive_summary.py`); the draft's all-status
  figures were replaced with their restated values (over-100% items,
  one-time buyers, LTV range, SP share, electronics freight and
  over-100% rate, Nov 2017 cohort size and LTV, month-1 retention,
  fully-observed cohort churn, AOV band, orders growth, top category
  share, at-risk customers) — the full old→new list is in
  `docs/publish_checklist.md` §6.
- The same restated basis was applied to the README and the
  one-pager the same day, so all three publish-facing documents
  agree (the Phase B/C/D analysis notes keep their all-status
  figures with their own basis — those are the analysis record,
  not the publish story).
- Remaining before publish: Power BI `.pbix` (needs a Windows
  machine — his PC or a later session) + the publish-day
  regression sweep + repo creation. Target live: Fri 27 Nov 2026.
