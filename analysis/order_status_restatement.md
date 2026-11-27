# Flagship 1 — Order-status restatement (Phase D, 10 Nov 2026)

The published headlines count every order in the fact table as
revenue, including orders that were later cancelled or never
available. This note restates the headlines two stricter ways and
says which definition the executive summary should use.

## Method

The star schema carries no order status (PLAN.md gap), so status
was loaded from the raw orders file (`data/raw/
olist_orders_dataset.csv`) into a staging table and joined to the
fact table — `sql/14_order_status_restatement.sql`, verified by
`src/check_order_status.py` (36 checks, 0 failures) and by an
independent pure-Python recompute from the raw CSVs. All three
sources agree to the cent and the customer. The live database was
never written to: the SQL file ran against a copy, the checker opens
it read-only with a TEMP staging table.

## Restated headline table (BRL, 2 decimals)

| Headline | All statuses (published) | Excl. cancelled + unavailable | Delivered only |
|---|---:|---:|---:|
| Orders with items | 98,666 | 98,199 (−467, −0.47%) | 96,478 (−2,188, −2.22%) |
| Fact rows | 112,650 | 112,101 (−549) | 110,197 (−2,453) |
| Revenue | 13,591,643.70 | 13,494,400.74 (−97,242.96, −0.72%) | 13,221,498.11 (−370,145.59, −2.72%) |
| Freight | 2,256,599.44 | 2,245,816.19 (−10,783.25, −0.48%) | 2,202,965.54 (−53,633.90, −2.38%) |
| Customers | 95,420 | 94,983 (−437, −0.46%) | 93,358 (−2,062, −2.16%) |
| Repeat buyers | 2,913 | 2,887 (−26, −0.89%) | 2,801 (−112, −3.84%) |
| Avg spend / customer | 142.44 | 142.07 (−0.37) | 141.62 (−0.82) |
| Churned / active | 66,802 / 28,618 | 66,476 / 28,507 | 65,170 / 28,188 |
| Churn rate | 70.01% | 69.99% | 69.81% |
| At-risk customers | 18,594 | 18,536 (−58) | 18,326 (−268) |
| Revenue at stake | 2,751,210.98 | 2,733,862.67 (−17,348.31, −0.63%) | 2,694,498.69 (−56,712.29, −2.06%) |
| At-risk repeat buyers | 617 | 611 (−6) | 600 (−17) |
| At-risk repeat revenue | 169,495.02 | 168,541.14 (−953.88, −0.56%) | 166,339.67 (−3,155.35, −1.86%) |

## Revenue by order status (fact rows only)

| Status | Orders | Fact rows | Revenue (BRL) | Freight (BRL) |
|---|---:|---:|---:|---:|
| delivered | 96,478 | 110,197 | 13,221,498.11 | 2,202,965.54 |
| shipped | 1,106 | 1,185 | 150,727.44 | 26,401.90 |
| canceled | 461 | 542 | 95,235.27 | 10,650.45 |
| invoiced | 312 | 359 | 61,526.37 | 7,462.38 |
| processing | 301 | 357 | 60,439.22 | 8,954.89 |
| unavailable | 6 | 7 | 2,007.69 | 132.80 |
| approved | 2 | 3 | 209.60 | 31.48 |
| **Total** | **98,666** | **112,650** | **13,591,643.70** | **2,256,599.44** |

Per-status orders, rows, revenue and freight sum exactly to the
published all-status headlines, and restated + excluded = published
to the cent — nothing is lost or created by the filter.

## The honest correction to the Phase A note

Phase A said cancelled + unavailable are "~1.24% of orders". That
figure is true of **all raw orders** (1,234 of 99,441 = 1.24%, re-derived
here, not copied) — but it overstates the revenue effect. Most of
those orders never reached the fact table at all: 767 of the 1,234
(603 unavailable, 164 cancelled) have no items and carried no
revenue. Only **467** cancelled/unavailable orders have items, worth
**BRL 97,242.96 — 0.72% of revenue**, not 1.24%. The restatement is
real but small: under one percent of revenue.

## What changes, what doesn't

- **Revenue: −0.72%.** Small, but it is the right number to quote —
  cancelled orders are not sales.
- **Churn: does not move.** Churn rate 70.01% → 69.99% (66,802 →
  66,476 churned). The Phase C churn story stands exactly as written.
- **At-risk: does not move.** 18,594 → 18,536 customers; revenue at
  stake 2,751,210.98 → 2,733,862.67 (−0.63%).
- **The recommendation: does not move.** The "retain the at-risk
  repeat buyers" move was built on 617 customers / BRL 169,495.02;
  restated it is 611 customers / BRL 168,541.14 (−6 customers,
  −BRL 953.88). Same move, same priority, slightly smaller number —
  the executive summary should quote **611 / BRL 168,541.14**.
- **Avg spend: 142.44 → 142.07.** The LTV anchor shifts by 37
  centavos; the flat-LTV range (BRL 131–167) is unaffected.

## Recommendation: which revenue definition for the executive summary

**Use "excluding cancelled + unavailable" (BRL 13,494,400.74) as the
headline revenue.** It is the revenue the business actually earned:
every order in it was placed and not cancelled, and the exclusion is
exactly the genuinely non-revenue part (BRL 97,242.96). Quote the
all-status figure (BRL 13,591,643.70) once, as a reconciliation
footnote, so a reader who re-adds the raw files lands on the same
total.

**Do not use delivered-only (BRL 13,221,498.11) as the headline.**
It is BRL 370,145.59 below the published figure, but only
BRL 97,242.96 of that is genuinely non-revenue. The other
BRL 272,902.63 is 1,721 in-flight orders (shipped 1,106, invoiced
312, processing 301, approved 2) — real orders in progress at the
cut-off date, not lost sales. Delivered-only understates the
business by 2.00 percentage points for no analytical gain.

## Caveats

- Status is taken from the raw orders file as downloaded 2 Nov 2026;
  it is a snapshot, not a live feed — an order marked "shipped" at
  download may have delivered since.
- The RFM segment map itself was not re-run under the restated
  definition in this step (segment boundaries are a judgement call,
  not a fact to reconcile). The inputs move by under 0.5% (437 of
  95,420 customers), so the segment conclusions stand; a full RFM
  re-run under the restated definition is a possible follow-up, not
  a blocker.
- The Nov 2016 gap check and the clean 2017–2018 trend are separate
  Phase D steps and are not covered here.
