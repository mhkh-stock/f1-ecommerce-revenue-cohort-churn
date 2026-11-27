# Flagship 1 — E-commerce Revenue, Cohort & Churn Analysis

**Status: LIVE — published 27 Nov 2026: https://github.com/mhkh-stock/f1-ecommerce-revenue-cohort-churn**
The analysis is complete and verified (558 checks, 0 failures); the
Power BI report link below is still empty until the `.pbix` is built
in Power BI Desktop (see `powerbi/publish-guide.md`).

**Dataset:** Olist Brazilian e-commerce, Sep 2016 – Aug 2018 (public
dataset, `olist/work-at-olist-data`). **Tools:** SQL (SQLite) · Python ·
Power BI. **Standard:** every headline number is reconciled three ways
— published analysis SQL, an independent SQL re-derivation, and a pure
Python recompute from the raw CSVs.

## The question

> Olist's Brazilian marketplace earned how much, from whom — and does
> it keep its customers?

## Headline (one sentence)

Olist earned **BRL 13,494,400.74** from **94,983 customers** across
**98,199 orders**, but it buys customers it does not keep: **97.0%
buy once**, lifetime value is flat at about **BRL 142** per customer,
and **69.99% have churned** — so the margin is in freight and
geography, not in loyalty.

## The numbers that carry the story

| Number | Value | Source |
|---|---:|---:|
| Revenue (restated — excludes cancelled + unavailable orders) | BRL 13,494,400.74 | `sql/14_order_status_restatement.sql` |
| Revenue as loaded (all statuses — reconciliation footnote) | BRL 13,591,643.70 | `sql/12_validation_reconciliation.sql` |
| Orders / customers (restated) | 98,199 / 94,983 | `sql/14` |
| Avg order value / avg spend per customer (restated) | BRL 137.42 / BRL 142.07 | `sql/14` |
| Fact rows (order items) | 112,650 | `sql/12` |
| Freight (delivery cost, restated) | BRL 2,245,816.19 — 16.64% of price | `sql/14` |
| Items costing more to deliver than they sell for | 4,100 of 112,650 (restated) | `sql/07`, `sql/14` |
| Worst freight category (500+ items) | `eletronicos` — 29.50% of price | `analysis/freight_by_category_findings.md` |
| Top state by revenue | São Paulo — 38.27% | `sql/05` |
| Peak month | Nov 2017 — BRL 1,003,862.14 | `sql/16_clean_trend_2017_2018.sql` |
| Clean trend | Jan 2017 → Aug 2018, BRL 13,449,529.68 | `sql/16` |
| Repeat buyers | 2,887 (3.04%) | `sql/14` |
| Churned customers | 66,476 (69.99%) | `sql/14` |
| At-risk repeat buyers worth saving | 611 — BRL 168,541.14 | `sql/11`, `sql/14` |
| Cohort LTV | flat BRL 131–163 per customer, 20 cohorts Jan 2017–Aug 2018 (restated) | model DB — page checks |

## What the data actually says

1. **Growth is volume, not basket size.** Revenue grew because more
   people ordered, not because anyone spent more: average order
   value stays near BRL 137 and LTV is flat across all 20 cohorts
   (Jan 2017–Aug 2018, restated).
2. **Discount cohorts do not retain.** The Nov 2017 Black Friday
   cohort is the largest ever (7,188 customers, BRL 1,008,457.51)
   but worth only BRL 140.30 each, and its month-1 retention
   (0.56%) is no better than October's (0.71%) — retention is
   near-zero everywhere, so the discount-cohort gap is invisible.
3. **Freight is the leak.** Freight eats 16.64% of price, and 4,100
   items cost more to deliver than they sell for. Electronics is
   the worst large category at 29.50%.
4. **Geography concentrates the business.** São Paulo alone is
   38.27% of revenue — growth outside SP is the cheapest new
   revenue available.
5. **Only 611 customers are plausibly saveable.** 18,536 customers
   look "at risk", but all but 611 of them bought exactly once —
   there is nothing to retain. The retention budget belongs to the
   611 repeat buyers holding BRL 168,541.14.

Full reasoning: `analysis/recommendations.md` (3 recommendations)
and `analysis/executive_summary.md` (2-page draft).

## The dashboard

**Power BI report: _not yet published_ — the `.pbix` is built in
Power BI Desktop from `powerbi/build-guide.md` (needs a Windows
machine); when it is published, the link goes here and the
verification checklist in `powerbi/publish-guide.md` §3 is ticked
against the live pages.**

Until then, the dashboard is fully specified and previewed:

| Page | What it shows | Preview |
|---|---|---|
| 1 — Overview | KPIs + monthly trend Jan 2017 → Aug 2018 + top categories | `outputs/page1_overview.png` |
| 2 — Where revenue leaks | Freight KPIs + freight-by-category + revenue by state | `outputs/page2_revenue_leak.png` |
| 3 — Cohorts & churn | Retention matrix + LTV + at-risk customers | `outputs/page3_cohorts_churn.png` |

Model: `powerbi/f1_powerbi.db` (star schema + `dim_order_status`;
rebuild with `python3 powerbi/build_model.py`). 12 DAX measures in
`powerbi/measures.dax`, every value verified in
`powerbi/verified_measures.json`. **No `.pbix` is bundled** — a
`.pbix` is a binary only Power BI Desktop can write; shipping one
would be faking it. The restatement is a measure-level filter, never
a deleted fact: the fact table keeps all 112,650 rows.

## How it is built (reproduce it)

```
data/raw/            Olist CSVs (public dataset — download script in src/)
  └─ README.md       What each file is + row counts as loaded
sql/schema.sql       Star schema (fact_order_items + 5 dimensions)
src/ingest.py        Staging → star, with counted DQ rejections
sql/01–02            Cohort sizes + retention matrix
sql/03–08            Revenue, freight, category, state, price distribution
sql/09               Cohort lifetime value
sql/10–11            RFM segments + churn analysis
sql/12               Validation: all 11 headlines reconciled 3 ways
sql/13               Per-cohort LTV re-check (matches Phase B exactly)
sql/14               Order-status restatement (the headline restated figures)
sql/15               Nov 2016 gap check (zero orders in the source file)
sql/16               Clean 2017–2018 trend (stops Aug 2018 — Sep 2018 is a 1-order stub)
powerbi/             Model + DAX + build guide + page layouts + publish guide
analysis/            One note per finding, each tied to its SQL
```

```bash
python3 src/ingest.py                 # builds data/processed/f1.db (112,650 rows)
python3 src/validate_headlines.py     # 11 checks — all headlines reconcile
python3 src/check_order_status.py     # 36 checks — restatement
python3 src/check_clean_trend.py      # 25 checks — clean trend
python3 src/check_powerbi_model.py    # 32 checks — DAX measure values
python3 src/check_dashboard_pages.py  # 29 checks — page layouts + previews
python3 src/check_phase_e_publish.py  # 70 checks — publish guide + this README
python3 src/check_architecture.py     # 62 checks — architecture diagram
python3 src/check_one_pager.py        # 46 checks — one-pager (md + pdf)
python3 src/check_executive_summary.py # 110 checks — executive summary final pass (restated)
python3 src/check_phase_f_polish.py   # checks — README polish + publish checklist
```

Architecture: `docs/architecture.mmd` (rendered as
`outputs/architecture_diagram.png`, notes in
`docs/architecture_notes.md`) — every pipeline step, file and
headline number traced end to end.

## Honest limits (read before quoting)

- **Nov 2016 is a stub, not a month.** The source file holds zero
  Nov 2016 orders; trend charts start Jan 2017. **Sep 2018 is a
  1-order stub** (16 raw orders, 15 cancelled) — the extract ends
  Aug 2018, so the trend stops there.
- **Restated vs as-loaded.** The headline excludes cancelled +
  unavailable orders (BRL 97,242.96, 0.72%). The as-loaded figure
  (BRL 13,591,643.70) is always shown as a footnote, never hidden.
- **Churn depends on the cut-off.** 69.99% under the locked
  2018-10-17 definition; 59.50% under a 2018-09-03 cut-off (see
  `analysis/rfm_churn.md`). The definition is stated, not buried.
- **NTILE frequency scores are meaningless here.** 92,096
  customers share frequency = 1, so segments use the recency
  score + actual order count (`analysis/rfm_churn.md`).
- **Two unrelated 611s.** 611 `eletronicos` items cost more to
  deliver than they sell for (22.18% of that category's 2,755
  items) — and, by coincidence, 611 at-risk repeat buyers hold
  BRL 168,541.14. Different things; never mix them.
- **Freight is a cost, never revenue.** Revenue = SUM(price) only,
  everywhere in this project.

## Project structure

```
f1-ecommerce-revenue-cohort-churn/
├── README.md                 ← this file (DRAFT until Phase F)
├── PLAN.md                   ← phases A–F + deadlines
├── sql/                      ← 16 query files + schema.sql
├── src/                      ← ingest + download + validate + 12 check scripts + 2 render scripts
├── analysis/                 ← 12 finding notes (incl. executive summary)
├── docs/                     ← architecture diagram source + notes + publish checklist
├── data/
│   ├── README.md             ← dataset note + load counts
│   ├── raw/                  ← Olist CSVs (downloaded, not uploaded)
│   └── processed/            ← f1.db (local only, not uploaded)
├── powerbi/                  ← model + DAX + guides + page layouts
└── outputs/                  ← 8 preview renders (3 page previews + 4 charts + architecture diagram)
```

`.db` files are never uploaded (rebuildable from the pushed
scripts). The Olist raw CSVs are not uploaded either — download
them with `src/download_olist.py`.
