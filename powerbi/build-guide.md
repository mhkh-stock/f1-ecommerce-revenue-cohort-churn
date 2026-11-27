# FLAGSHIP 1 — Phase E: Power BI dashboard build guide (14 Nov 2026)

**Model:** `powerbi/f1_powerbi.db` — the Olist star schema plus
`dim_order_status` and `order_status` on the fact table. Rebuild any
time with `python3 powerbi/build_model.py` (reads
`data/processed/f1.db` read-only + `data/raw/olist_orders_dataset.csv`).
**No `.pbix` is bundled:** a `.pbix` is a binary only Power BI
Desktop can write — shipping one would be faking it. This guide
builds it in Power BI Desktop in ~20 minutes from the model below.
**Verified values:** `powerbi/verified_measures.json` (every DAX
measure re-checked by `src/check_powerbi_model.py`).

## 1. Import the model

1. Power BI Desktop → Get Data → SQLite / ODBC → `f1_powerbi.db`.
   Import all 6 tables: `fact_order_items`, `dim_customer`,
   `dim_product`, `dim_seller`, `dim_date`, `dim_order_status`.
2. In Power Query, add one calculated column to `dim_date`:
   `order_year_month = Text.Start([date_id], 7)` — gives `2017-01` …
   `2018-08` for the trend axis. (The fact table's `date_id` is text
   `YYYY-MM-DD`; Power BI will not auto-detect it as a date.)
3. Mark `dim_date[date_id]` as a date table (Modeling → Mark as Date
   Table) so time-intelligence works.

## 2. Relationships (all single direction, fact → dimension)

| From | To | Cardinality |
|---|---|---|
| `fact_order_items[customer_id]` | `dim_customer[customer_id]` | Many to one |
| `fact_order_items[product_id]` | `dim_product[product_id]` | Many to one |
| `fact_order_items[seller_id]` | `dim_seller[seller_id]` | Many to one |
| `fact_order_items[date_id]` | `dim_date[date_id]` | Many to one |
| `fact_order_items[order_status]` | `dim_order_status[order_status]` | Many to one |

Cross-filter direction: Single for all five. Do NOT turn on
bi-directional filtering — it double-counts customers across states.

## 3. Measures

Paste `powerbi/measures.dax` into Modeling → New measure, one at a
time. The restatement lives in the measures, not in the fact table:
every headline measure filters `dim_order_status[is_restated] = 1`
(cancelled + unavailable excluded, `sql/14`). The fact table keeps
all 112,650 rows so the all-status footnote (BRL 13,591,643.70) stays
provable. Format: revenue/freight as currency (BRL, 2 dp), rates as
percentages (2 dp).

## 4. The three pages

### Page 1 — Overview (the executive page)
- KPI cards (top row): Total Revenue (Restated) **BRL 13,494,400.74** ·
  Total Orders (Restated) **98,199** · Total Customers (Restated)
  **94,983** · Avg Order Value **BRL 137.42** · Churn Rate **69.99%**.
- Line chart: monthly revenue, Jan 2017 → Aug 2018 (clean trend,
  `sql/16`). Add a text box: "2016 is a 329-order pilot stub and Sep
  2018 is a 1-order stub — the trend starts Jan 2017 and stops Aug
  2018." (`outputs/preview_monthly_revenue.png` is the same chart.)
- Bar chart: revenue by product category, top 10.
- Slicer: `dim_date[order_year]` and `dim_order_status[is_restated]`
  (default = restated only, so a reader cannot accidentally quote
  the all-status figure as earned revenue).
- Footnote text box: "Revenue excludes cancelled + unavailable
  orders (BRL 97,242.96, 0.72%). As loaded, all statuses:
  BRL 13,591,643.70."

### Page 2 — Where revenue leaks
- KPI cards: Total Freight (Restated) **BRL 2,245,816.19** · Freight %
  of Revenue **16.64%** · Items Over 100% Freight **4,100**.
- Bar chart: freight % of price by category, top 10 among categories
  with 500+ items — electronics (`eletronicos`) first at 29.50%
  restated (29.07% all-status, Phase A). Tiny categories show extreme
  rates on tiny bases (e.g. `casa_conforto_2` 53.97% on 30 items) and
  are excluded from this chart by the 500-item rule — see
  `analysis/freight_by_category_findings.md` finding 3.
- Bar chart: revenue by customer state, top 10 — SP **38.27%**.
- Scatter: item price vs freight value (sample 5,000 points) — the
  cloud above the diagonal is the 4,100 items that cost more to
  deliver than they sell for.

### Page 3 — Cohorts & churn
- KPI cards: Repeat Buyer Rate **3.04%** · Churn Rate **69.99%** ·
  Saveable at-risk revenue **BRL 168,541.14** (611 repeat buyers).
- Matrix visual: cohort retention, rows = first-purchase month,
  columns = months since first purchase, values = % retained
  (`sql/02` output — paste as a static table; Power BI has no native
  cohort matrix).
- Bar chart: LTV by cohort — flat BRL 131–167, the "size bought
  revenue, not better customers" story (`sql/09` / `sql/13`).
- Text box with the honest caveat: "Retention in month 1 is 0.55%
  (Nov 2017) vs 0.70% (Oct 2017) — the discount-cohort gap is
  invisible because retention is near-zero everywhere."

## 5. Publish

File → Publish → the workspace, then paste the report link into the
flagship README (Phase F). Before publishing, run
`python3 src/check_powerbi_model.py` — it re-checks every measure
value in this guide against the model database.

## Limits — what this dashboard does not do

- **No live connection.** The model is a static SQLite import of the
  Olist extract (Sep 2016 – Aug 2018). A real client wires DirectQuery
  to their warehouse; the measures transfer unchanged.
- **Churn Rate is a verified constant (0.6999), not a live DAX
  calculation** — the 6-month lookback needs a calculated column the
  guide does not build. If the model is refreshed with new data,
  re-run `build_model.py` and update the constant.
- **The cohort matrix is a pasted table**, not a live visual — Power
  BI has no native cohort matrix; the numbers come from `sql/02`.
