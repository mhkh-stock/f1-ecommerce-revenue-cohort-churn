# Flagship 1 — Phase D validation notes (8 Nov 2026)

Every headline number reconciled a second way — and a third way.
Three sources: **(a)** the published Phase B/C number, **(b)** an
independent SQL re-derivation (`sql/12_validation_reconciliation.sql`,
written differently from the Phase B/C queries: set difference instead
of `CASE` on `MAX(date)`, `HAVING` instead of window counts),
**(c)** a pure-Python recompute straight from the raw Olist CSVs
(`src/validate_headlines.py` — no database, no ingest script).

## Reconciliation table

| Headline | Published (B/C) | SQL re-derive | Python re-derive | Match |
|---|---:|---:|---:|:---:|
| Fact rows | 112,650 | 112,650 | 112,650 | ✓ |
| Orders with items | 98,666 | 98,666 | 98,666 | ✓ |
| Revenue (BRL) | 13,591,643.7 | 13,591,643.7 | 13,591,643.7 | ✓ |
| Freight (BRL) | 2,256,599.44 | 2,256,599.44 | 2,256,599.44 | ✓ |
| Customers with a purchase | 95,420 | 95,420 | 95,420 | ✓ |
| Churned customers | 66,802 | 66,802 | 66,802 | ✓ |
| Active customers | 28,618 | 28,618 | 28,618 | ✓ |
| Repeat buyers | 2,913 | 2,913 | 2,913 | ✓ |
| At-risk customers | 18,594 | 18,594 | 18,594 | ✓ |
| Revenue at stake (BRL) | 2,751,210.98 | 2,751,210.98 | 2,751,210.98 | ✓ |
| Avg spend per customer (BRL) | 142.44 | 142.44 | 142.44 | ✓ |

**Verdict: ALL 11 HEADLINES RECONCILE.**
Run: `python3 src/validate_headlines.py` (11 checks passed,
0 failed).

## What the second ways caught

- Nothing material: all three sources agree to the cent / the
  customer on all 11 headlines. The Phase B/C numbers stand as
  published.
- The churn definition is the one place the three sources could
  have diverged (cut-off 2018-10-17, churn = last purchase before
  2018-04-17): the Python path recomputes last-purchase dates from
  the raw orders file, the SQL path uses set difference on the star
  schema, and both land on 66,802 churned / 28,618 active.
- The 16 cancelled orders after 2018-09-03 (no items) appear in
  neither the Python nor the SQL recompute — both go through
  item-bearing rows only — so the +44-day recency floor documented
  in Phase C is a property of the dataset, not of the query path.
  The cut-off sensitivity (churn 59.50% under a 2018-09-03 cut-off)
  still stands as reported in Phase C.

## What is NOT validated here

- The Phase C segment map (9 named segments) — counts sum to
  95,420 and revenue sums to BRL 13,591,643.70 inside
  `src/check_rfm.py`, but the segment *boundaries* are a judgement
  call (R score + actual order count), not a fact to reconcile.
  The executive summary will state the boundary rule, not just the
  segment names.
- The LTV-by-cohort range (BRL 131–167) — the overall average
  (BRL 142.44) reconciles here; per-cohort LTV is re-checked in
  the Phase D insights step from `sql/09_cohort_lifetime_value.sql`.
