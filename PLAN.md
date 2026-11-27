# FLAGSHIP 1 — PLAN (prep note, 31 Oct 2026 — build starts Mon 2 Nov 2026)

**Project:** E-commerce Revenue, Cohort & Churn Analysis
**Tools:** SQL · Python (pandas) · Power BI · **Deadline: Fri 27 Nov 2026**
**Status:** Ingest DONE (2 Nov 2026, verified above); analysis execution
plan locked 2 Nov 2026 night; analysis builds start Tue 3 Nov 2026.

## Business questions (Master Plan §4)

1. Where does revenue leak?
2. Which customer cohorts retain, which churn, and what are they worth (RFM)?
3. What 3 moves lift margin?

## Dataset

Olist Brazilian e-commerce (100k orders, multi-table — real joins, real mess).
Public dataset; download link and licence recorded in `data/README.md` at build time.
If Olist proves awkward to fetch, fallback = the same shape on a smaller public
retail dataset — decided at build time, noted in the README, never silently swapped.

## Build shape (pro standard, Master Plan §3.2)

- Data loaded into PostgreSQL with a star schema: `fact_orders` + dimensions
  (customers, products, sellers, dates).
- SQL query pack (numbered, one business question per file): CTEs, window
  functions, cohort retention, RFM.
- Data-quality checks as code (`src/checks.py` style, as in the plan).
- Cohort + RFM notebooks (numbered: 01_cleaning → 02_eda → 03_analysis).
- Power BI dashboard fed from the database (live link + screenshots).
- 2-page executive summary with 3 recommendations + architecture diagram.
- One-pager (`outputs/one-pager.pdf`) for interviews and shares.

## Study findings (verified 2 Nov 2026, from the live database)

Star schema is real and loaded (`data/processed/f1.db`, SQLite):
`fact_order_items` 112,650 rows (order_id, order_item_id, customer_id,
product_id, seller_id, date_id, price, freight_value); `dim_customer` 99,441
rows / 96,096 unique people; `dim_product` 32,951; `dim_seller` 3,095;
`dim_date` 634. Purchase dates in fact: 2016-09-04 → 2018-09-03
(616 distinct days). Item revenue SUM(price) = BRL 13,591,643.70
(reconciles exactly to the ingest record); freight SUM = BRL 2,256,599.44
(kept separate — freight is delivery cost, not seller revenue).
Repeat buyers ≈ 3,000 unique people (~3%) — this is a one-time-buyer
business; retention, not acquisition, is the story.

Two honest gaps the analysis must handle, not hide:
1. **No order status in the schema.** The 5 tables carry no
   delivered/cancelled flag, so cancellation-driven revenue leak cannot be
   measured from the current load. Phase A decides: either load order
   status as one extra dimension from the Olist orders file, or scope Q1
   to price/freight/category/state leakage only and say so in the README.
2. **Repeat buyers must be counted via `customer_unique_id`, not
   `customer_id`.** Raw `customer_id` is near-unique per order
   (98,666 distinct for 98,666 orders); counting it would falsely show
   zero repeat buyers. Cohort and RFM logic joins through `dim_customer`
   on `customer_unique_id`.

## Execution plan (3–27 Nov 2026) — starts Tue 3 Nov daily run

Not a rushed 1-day build: one analysis block per step, each verified
before the next, alongside the daily small builds.

- **Phase A, Nov 3–4 — Revenue leak pack.** Monthly revenue trend;
  revenue by category / state / seller; freight burden (freight as % of
  price, high-freight low-price orders); price distribution. Plus the
  order-status decision above.
- **Phase B, Nov 5–6 — Cohort retention.** Monthly cohorts by first
  purchase month (via `customer_unique_id`); retention matrix;
  cohort lifetime value.
- **Phase C, Nov 7–8 — RFM + churn.** Recency / frequency / monetary
  segments; churn defined as no purchase in 6 months; at-risk list.
- **Phase D, Nov 9–13 — Validation + insights.** Every headline number
  reconciled a second way; 3 recommendations drafted; executive summary
  skeleton. First block DONE 8 Nov 2026 (pulled forward a day):
  `sql/12_validation_reconciliation.sql` + `src/validate_headlines.py`
  + `analysis/validation_notes.md` — all 11 headlines reconcile across
  THREE sources (published Phase B/C number = independent SQL
  re-derivation = pure-Python recompute from the raw Olist CSVs):
  112,650 fact rows, 98,666 orders, BRL 13,591,643.70 revenue,
  BRL 2,256,599.44 freight, 95,420 customers, churned 66,802 / active
  28,618, 2,913 repeat buyers, at-risk 18,594 / BRL 2,751,210.98,
  avg spend BRL 142.44 (11 checks, 0 failures). Two fixes on the way:
  correlated NOT EXISTS churn query was far too slow (killed twice) —
  rewritten as set-difference scans (10.6 s for all six queries); the
  validator's statement splitter first dropped the Q1 query with the
  file header comment (fixed: strip comments before skipping empties).
  Next Phase D blocks (Mon 9 Nov): per-cohort LTV re-check + the 3
  recommendations + executive summary skeleton. DONE 9 Nov 2026:
  `sql/13_cohort_ltv_recheck.sql` (temp tables + strftime + interval
  retention — a different code path from sql/09) + `src/check_ltv_recheck.py`
  (pure-Python recompute from the raw Olist CSVs, 13 checks, 0 failures)
  — all 23 cohorts match the published Phase B LTV exactly
  (customers, repeat buyers, revenue, LTV), retention Oct–Dec 2017
  matches, flat-LTV range confirmed BRL 131.60–167.07 (overall
  BRL 142.44); `analysis/recommendations.md` (3 moves: electronics
  freight pricing first, grow outside São Paulo, retain the 617
  at-risk repeat buyers only — report "revenue at risk" as
  BRL 169,495.02, never BRL 2.75M) + `analysis/executive_summary_skeleton.md`
  (2-page skeleton with the story, the 3 moves and the caveats).
  Remaining Phase D: Nov 2016 gap check DONE 11 Nov 2026
  (`sql/15_nov2016_gap_check.sql` + `src/check_nov2016_gap.py` +
  `analysis/nov2016_gap_check.md`, 26 checks, 0 failures — the
  gap is in the source itself: the raw Olist orders file holds
  ZERO November 2016 orders; 2016 is a 329-order pilot fragment,
  BRL 49,785.92, 0.37% of revenue; decision locked: trend charts
  start Jan 2017, 2016 shown only as a labelled stub, the three
  micro-cohorts stay in the matrix with a footnote) + clean
  2017–2018 trend.
- **Phase E, Nov 14–20 — Power BI dashboard.** Model from the star
  schema + DAX measures; screenshots; build guide. First block DONE
  14 Nov 2026 (`powerbi/build_model.py` + `powerbi/measures.dax` +
  `powerbi/build-guide.md` + `powerbi/README.md` +
  `src/render_powerbi_previews.py` + `src/check_powerbi_model.py`,
  32 checks, 0 failures): model DB `powerbi/f1_powerbi.db` is the
  star schema plus `dim_order_status` and `order_status` on the fact
  table (112,650 rows, 0 without a status, 8 statuses, exactly 2
  excluded); the restatement is a MEASURE-level filter — the fact
  table keeps every row, so the all-status footnote
  (BRL 13,591,643.70) stays provable; 12 DAX measures with verified
  values (restated revenue BRL 13,494,400.74, orders 98,199,
  customers 94,983, freight BRL 2,245,816.19 / 16.64%, AOV BRL 137.42,
  avg spend BRL 142.07, repeat buyers 2,887 / 3.04%, churn 69.99%
  = 66,476 — matches sql/14 exactly, items over 100% freight 4,100,
  SP share 38.27%, peak Nov 2017 BRL 1,003,862.14); 4 preview renders
  in `outputs/` (monthly trend reconciles to the sql/16 clean total
  BRL 13,449,529.68); build guide covers 3 pages (Overview / leak /
  cohorts & churn) + relationships + ~20-min steps. No `.pbix`
  bundled (honestly noted — Power BI Desktop authors it from this
  model). Remaining Phase E: build the `.pbix` in Power BI Desktop
  (needs a Windows machine — Hashir's PC or a later session) and
  paste the published report link into the flagship README in
  Phase F. Third block DONE 16 Nov 2026 (`powerbi/publish-guide.md`
  + flagship `README.md` DRAFT + `src/check_phase_e_publish.py`,
  70 checks, 0 failures): publish steps, 16-row checklist against
  `verified_measures.json`, sharing steps; README draft carries
  every verified headline with the report-link slot honestly empty
  until the `.pbix` exists.
- **Phase F, Nov 21–26 — README + one-pager + review + publish.**
  Architecture diagram, 2-page executive summary, one-pager, second-pass
  review, then publish: browser-create repo → App text push → browser
  binary upload → byte-size verification → profile library table update.
- **Fri 27 Nov: LIVE** (deadline; may go live early if Phase F finishes
  early — never by cutting verification).

## Why this order

Flagship 1 is the #1 portfolio shape recruiters name (Master Plan §4), and
the daily market watch keeps revalidating its exact stack: SQL ~62%,
Power BI ~40% vs Tableau ~16%, Data Quality ~41–42% of London DA ads
through October 2026. Nothing in the plan needs changing before the build.
