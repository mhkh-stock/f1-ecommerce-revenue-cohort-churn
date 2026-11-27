# FLAGSHIP 1 — Phase E (block 2, 15 Nov 2026): dashboard page layouts

**Model:** `powerbi/f1_powerbi.db` · **Measures:** `powerbi/measures.dax`
(all verified in `powerbi/verified_measures.json`) ·
**Build guide:** `powerbi/build-guide.md` (import, relationships, measures,
publish steps — this file adds the exact per-page layout so the `.pbix`
can be built in Power BI Desktop without re-deciding anything).
**Page previews:** `outputs/page1_overview.png`,
`outputs/page2_revenue_leak.png`, `outputs/page3_cohorts_churn.png`
(rendered by `src/render_dashboard_pages.py` from the same model DB —
the numbers on the previews are the numbers the pages must show).
**Checks:** `src/check_dashboard_pages.py` re-verifies every KPI and
every chart total on all three pages against the model DB.

## Canvas and shared rules

- Canvas 16:9 (1280 × 720). One slicer bar across the top of every
  page: `dim_date[order_year]` (2017, 2018) + `dim_order_status[is_restated]`
  (default = restated only). Every visual on every page filters on the
  restated measure set — a reader cannot accidentally quote the
  all-status figure (BRL 13,591,643.70) as earned revenue.
- KPI cards: one row, top of page, equal width, value in bold 28 pt,
  label 11 pt, subtitle 9 pt with the definition (e.g. "excl. cancelled
  + unavailable"). Currency BRL, 2 dp on cards; percentages 2 dp.
- Footnote bar at the bottom of every page (9 pt grey):
  "Source: Olist Brazilian e-commerce extract, Sep 2016 – Aug 2018.
  Revenue excludes cancelled + unavailable orders (BRL 97,242.96,
  0.72%). All-status total BRL 13,591,643.70."
- Colour rule: single accent (#1F4E79) for bars/lines; the Nov 2017
  peak bar/point highlighted in orange (#ED7D31) — the only highlight
  colour on the report, so it always means "the Black Friday peak".

## Page 1 — Overview (the executive page)

| Slot | Visual | Field / measure | Verified value |
|---|---|---|---|
| KPI 1 | Card | Total Revenue (Restated) | BRL 13,494,400.74 |
| KPI 2 | Card | Total Orders (Restated) | 98,199 |
| KPI 3 | Card | Total Customers (Restated) | 94,983 |
| KPI 4 | Card | Avg Order Value | BRL 137.42 |
| KPI 5 | Card | Churn Rate | 69.99% |
| Main | Line chart | Monthly revenue, Jan 2017 → Aug 2018 (clean trend, `sql/16`) | Total BRL 13,449,529.68; peak Nov 2017 BRL 1,003,862.14 |
| Side | Bar chart | Revenue by product category, top 10 | Top: beleza_saude BRL 1,255,695.13 |
| Text | Text box | "2016 is a 329-order pilot stub and Sep 2018 is a 1-order stub — the trend starts Jan 2017 and stops Aug 2018." | — |

## Page 2 — Where revenue leaks

| Slot | Visual | Field / measure | Verified value |
|---|---|---|---|
| KPI 1 | Card | Total Freight (Restated) | BRL 2,245,816.19 |
| KPI 2 | Card | Freight % of Revenue | 16.64% |
| KPI 3 | Card | Items Over 100% Freight | 4,100 |
| Main | Bar chart | Freight % of price by category, top 10 (categories with 500+ items — tiny categories excluded, see findings note 3) | First: eletronicos 29.50% restated (29.07% all-status) |
| Side | Bar chart | Revenue by customer state, top 10 | SP 38.27% |
| Lower | Scatter (5,000-pt sample) | Item price (x) vs freight value (y); diagonal = freight = price | 4,100 points sit above the diagonal |

## Page 3 — Cohorts & churn

| Slot | Visual | Field / measure | Verified value |
|---|---|---|---|
| KPI 1 | Card | Repeat Buyer Rate | 3.04% |
| KPI 2 | Card | Churn Rate | 69.99% |
| KPI 3 | Card | Saveable at-risk revenue | BRL 168,541.14 (611 repeat buyers) |
| Main | Matrix (pasted table) | Cohort retention, rows = first-purchase month, columns = months since first purchase, values = % retained (`sql/02`) | Month-1 retention 0.56% (Nov 2017) vs 0.71% (Oct 2017), restated (0.55% / 0.70% all-status) |
| Side | Bar chart | LTV by cohort — flat BRL 131–163 restated (BRL 131–167 all-status) | Overall BRL 142.07 per customer (restated); mean of cohort LTVs BRL 144.05 |
| Text | Text box | "Retention in month 1 is 0.56% (Nov 2017) vs 0.71% (Oct 2017) — the discount-cohort gap is invisible because retention is near-zero everywhere." | — |

## What is NOT on the pages (limits, from the build guide)

- No live connection (static SQLite import). No `.pbix` is bundled —
  the `.pbix` is authored in Power BI Desktop from this spec (Phase E
  remaining step, needs a Windows machine — his PC or a later session).
- Churn Rate is a verified constant (0.6999), not a live DAX measure.
- The cohort matrix is a pasted table, not a live visual.

## Change log

- 15 Nov 2026 (Phase E block 2): page layouts specified + 3 page
  previews rendered + page checks written. Remaining Phase E: build
  the `.pbix` in Power BI Desktop + paste the published report link
  into the flagship README (Phase F, 21–26 Nov).
