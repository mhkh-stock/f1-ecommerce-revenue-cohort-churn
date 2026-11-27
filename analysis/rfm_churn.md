# Flagship 1 — RFM segments + churn (Phase C, 7 Nov 2026)

From `sql/10_rfm_segments.sql` and `sql/11_churn_analysis.sql`, run on
the real star schema (`data/processed/f1.db`, 112,650 fact rows).
Revenue = SUM(price) only; freight is delivery cost, never revenue.
Customers are counted by `customer_unique_id` throughout.
Verified by `src/check_rfm.py`: 30 checks, 0 failures.

## Method

- **Cut-off ("today"): 2018-10-17**, the dataset end, per the locked
  definitions in `cohort_definitions.md`. Churn = no purchase in the
  6 months before the cut-off (last purchase before 2018-04-17).
  At-risk = last purchase 3–6 months before the cut-off
  (2018-04-17 to 2018-07-17).
- **RFM per unique customer:** Recency = days from last purchase to
  2018-10-17; Frequency = order count; Monetary = total spend.
  Quintile scores 1–5 via `NTILE(5)`; R is reversed so 5 is most
  recent. Segments are built from R score plus the **actual order
  count**, not from the F score — see the F-score warning below.
- **One data caveat, stated up front:** the last item-bearing
  purchase is 2018-09-03. The 16 orders after that date are all
  cancelled with no items, so the 44 days to 2018-10-17 are dead
  time: no customer could have bought in them, and every recency
  carries a +44-day floor. The churn sensitivity to this choice is
  measured in §4 (Q6), not hidden.

## 1. RFM base — the numbers everything else reconciles to

- Customers with at least one purchase: **95,420**. Orders: **98,666**.
  Revenue: **BRL 13,591,643.70**. Overall average spend per customer:
  **BRL 142.44** (matches the Phase B lifetime value exactly).
- Recency: mean **287.5 days**, range **44–773 days**. Only **9,515**
  customers (9.97%) bought within the last 90 days; **27,805**
  (29.14%) within 180 days; **67,311** (70.54%) within a year.
  Read plainly: the average customer last bought more than nine
  months before the cut-off.

### Quintile boundaries (19,084 customers per score, by construction)

| Score | R — days since last purchase | F — orders | M — BRL spent |
|---|---|---|---|
| 1 | 433–773 | 1 | 0.85–39.90 |
| 2 | 317–433 | 1 | 39.90–69.90 |
| 3 | 226–317 | 1 | 69.90–109.90 |
| 4 | 142–226 | 1 | 109.90–179.90 |
| 5 | 44–142 | 1–16 | 179.90–13,440.00 |

Two things to notice. First, R5 (most recent) means a last purchase
between 2018-05-29 and 2018-09-03 — "recent" in this business is
still up to five months ago. Second, the shared edge values (recency
433 sits in both R1 and R2; BRL 39.90 in both M1 and M2) are
same-value ties split across adjacent quintiles by `NTILE`, not real
differences between the customers on either side.

### The F-score warning — why segments do not use F score

`NTILE(5)` over frequency forces ~19,084 customers into each bucket
even though **92,507 customers share the identical value
frequency = 1**. The result (Q4): buckets F1–F4 are 100% one-time
buyers, and F5 mixes **16,171 one-time buyers** with all **2,913**
repeat buyers. An F score of 5 therefore says nothing about repeat
behaviour here — a one-time buyer with F = 5 is indistinguishable
from one with F = 1. Any segment map built on F score would label
~16,000 one-time buyers "Champions". The segment map below uses
the actual order count instead, and the NTILE F score is kept in the
query only as a documented diagnostic.

## 2. Segments — nine, exhaustive, mutually exclusive

| Segment | Customers | Share | Revenue (BRL) | Rev. share | Avg spend (BRL) | Avg recency (days) |
|---|---:|---:|---:|---:|---:|---:|
| Recent One-Time | 36,923 | 38.70% | 5,197,945.66 | 38.24% | 140.78 | 139.5 |
| Lost | 18,626 | 19.52% | 2,590,812.41 | 19.06% | 139.10 | 523.9 |
| At-Risk One-Time | 18,496 | 19.38% | 2,635,404.28 | 19.39% | 142.49 | 365.7 |
| Fading One-Time | 18,462 | 19.35% | 2,404,189.49 | 17.69% | 130.22 | 269.4 |
| Loyal | 1,117 | 1.17% | 277,634.98 | 2.04% | 248.55 | 137.5 |
| Potential Loyalists | 622 | 0.65% | 158,616.09 | 1.17% | 255.01 | 265.3 |
| At-Risk | 588 | 0.62% | 153,619.78 | 1.13% | 261.26 | 366.0 |
| Hibernating | 458 | 0.48% | 114,708.54 | 0.84% | 250.46 | 514.5 |
| Champions | 128 | 0.13% | 58,712.47 | 0.43% | 458.69 | 135.9 |
| **Total** | **95,420** | **100%** | **13,591,643.70** | **100%** | **142.44** | — |

Definitions: Champions = R 4–5 and 3+ orders; Loyal = R 4–5 and
2 orders; Potential Loyalists = R 3 and 2+ orders; Recent One-Time
= R 4–5 and 1 order; Fading One-Time = R 3 and 1 order; At-Risk =
R 2 and 2+ orders; At-Risk One-Time = R 2 and 1 order; Hibernating
= R 1 and 2+ orders; Lost = R 1 and 1 order.

The honest reading:

1. **Four one-time segments hold 96.95% of customers and 94.38% of
   revenue (92,507 customers, BRL 12,828,351.84).** The segment names
   mostly describe *when* someone bought once, not a loyalty ladder:
   "Recent One-Time" (38.70%) vs "Lost" (19.52%) is a recency split
   of the same behaviour.
2. **All five repeat-buyer segments together are 2,913 customers
   (3.05%) and BRL 763,291.86 (5.62% of revenue).** Repeat buyers do
   spend more — BRL 262.03 on average vs BRL 138.67 for one-time
   buyers — but there are too few of them for that gap to move the
   business.
3. **Champions is 128 people (0.13%), worth BRL 58,712.47.**
   Their average spend (BRL 458.69) is 3.2× the overall average —
   the only segment where "best customers" means something — but 128
   people cannot carry a retention strategy.
4. **Average spend is flat across the one-time segments
   (BRL 130.22–142.49).** Recency does not predict spend for
   one-time buyers: a customer who bought once 18 months ago spent
   about the same as one who bought once last month.

## 3. Churn — 70.01% churned, and what that actually means

| Status | Customers | Share | Revenue (BRL) | Rev. share | Avg spend (BRL) |
|---|---:|---:|---:|---:|---:|
| Churned (no purchase in 6 months) | 66,802 | 70.01% | 9,431,459.95 | 69.39% | 141.19 |
| Active (purchase within 6 months) | 28,618 | 29.99% | 4,160,183.75 | 30.61% | 145.37 |
| **Total** | **95,420** | **100%** | **13,591,643.70** | **100%** | **142.44** |

Churned + active reconciles exactly to 95,420 customers and
BRL 13,591,643.70. Note the average spend is nearly identical for
churned (BRL 141.19) and active (BRL 145.37) customers — churn is
not concentrated among low spenders; it is spread evenly, because
almost everyone churns.

### Churn by first-purchase cohort year

| Cohort year | Customers | Churned | Churn rate | Churned revenue (BRL) |
|---:|---:|---:|---:|---:|
| 2016 | 309 | 305 | 98.71% | 50,380.92 |
| 2017 | 43,220 | 42,889 | 99.23% | 6,153,202.55 |
| 2018 | 51,891 | 23,608 | 45.50% | 3,227,876.48 |

The 2016 and 2017 cohorts are the honest comparison: **98.71% and
99.23% churned**. Given a full year or more of follow-up, essentially
every customer from those years is gone. The 2018 rate (45.50%) is
a censoring artefact, not better retention: most 2018 first-buyers
bought within 6 months of the cut-off, so they count as "active" by
construction — they simply have not had time to churn yet. Phase B
found the same pattern in repeat share, which falls from 2.46%
(Mar 2018 cohort) to 0.56% (Aug 2018) for the same reason.

### At-risk — BRL 2.75M "at stake", of which BRL 169,495 is real

- At-risk customers (last purchase 3–6 months ago): **18,594**
  (19.49% of all customers, 64.97% of active customers).
  Revenue attached: **BRL 2,751,210.98** (20.24% of total revenue),
  average **BRL 147.96**, across **19,298** orders.
- The split (Q4) is the important part:

| At-risk group | Customers | Revenue at stake (BRL) |
|---|---:|---:|
| Repeat buyers — plausibly saveable | 617 | 169,495.02 |
| One-time buyers — phantom at stake | 17,977 | 2,581,715.96 |

Only **6.16%** of the at-risk revenue belongs to repeat buyers.
The other 93.84% belongs to one-time buyers whose single purchase
was 3–6 months ago — and one-time buyers return at ~0.5%, so that
BRL 2,581,715.96 is not revenue at risk of being lost; it is revenue
that was never going to repeat. The top-25 at-risk list (Q5) makes
the same point from the other side: all 25 are one-time buyers,
headed by a single BRL 7,160.00 order from 2018-07-15. The
saveable at-risk figure is **617 customers, BRL 169,495.02**.

Two more counts for the record: **1,955 repeat buyers are already
churned** (BRL 501,622.56 of past spend — the lost repeat base),
and only **10,024 customers** bought within the last 3 months
(BRL 1,408,972.77, 10.37% of revenue).

## 4. Cut-off sensitivity — the honest churn range

The 2018-10-17 cut-off is the locked definition, but the last
item-bearing purchase is 2018-09-03. If the cut-off were 2018-09-03
instead, **10,026 customers** would flip from churned to active and
churn would be **56,776 customers (59.50%)** instead of 66,802
(70.01%). The honest statement is therefore a range: churn is
**59.50–70.01%**, with 70.01% the headline under the locked
definition. The 10.5-point gap is entirely an artefact of 44 dead
days in which no purchase could occur; it does not change the
conclusion, since even the low end says three in five customers
never return.

## 5. What RFM and churn mean in a one-time-buyer business

The Phase B headline stands and Phase C sharpens it: this business
buys customers, it does not keep them. RFM here is a description of
*when* people bought once, not a ladder of loyalty — the segments
that sound valuable (Champions, Loyal) hold 1,245 people between
them, while "Lost" alone holds 18,626. Churn is not customers
drifting away over months; it is customers never returning after the
first order (96.9% one-time buyers, 98.71–99.23% churn in the
fully-observed 2016–2017 cohorts).

What this implies for Phase D (recommendations):

1. **Lead with acquisition economics and freight, not loyalty.**
   With LTV flat at BRL 142.44 and retention near zero, a loyalty
   programme would address 2,913 people. The Phase A margin story
   (freight 16.6% of price; 4,119 items where freight exceeds price)
   touches every order instead.
2. **Any retention spend targets the 617 at-risk repeat buyers
   only** — the one plausibly saveable group, worth BRL 169,495.02.
   Win-back aimed at the other 17,977 at-risk customers would spend
   against a ~0.5% return rate.
3. **Do not report "revenue at risk" as BRL 2.75M.** The defensible
   figure is BRL 169,495.02; the rest is one-time revenue that was
   never going to repeat. A dashboard that shows the bigger number
   without the split would mislead whoever reads it.

## Phase C status: COMPLETE

RFM segments + churn (7 Nov 2026) → Phase D (validation +
insights, 9–13 Nov) next. Files: `sql/10_rfm_segments.sql`,
`sql/11_churn_analysis.sql`, `src/check_rfm.py` (30 checks, all
passing), this write-up. No publish in this step — local build only.
