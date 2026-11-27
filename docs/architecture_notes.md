# Flagship 1 — Architecture notes (Phase F prep, 17 Nov 2026, DRAFT)

Companion to `docs/architecture.mmd` (renders as `outputs/architecture_diagram.png`).
Every claim in the diagram is checked by `python3 src/check_architecture.py`.

## The six layers, in plain words

1. **Source — raw data.** The dataset is the real, public Brazilian Olist
   e-commerce extract (Sep 2016 – Aug 2018), downloaded from the official
   Olist repo — five CSVs, not a clean classroom file. Nothing here is
   invented or sampled.
2. **Ingest — load + data-quality checks.** `src/ingest.py` stages the CSVs
   first and only then writes the star schema, rejecting rows with missing
   keys, negative prices or missing order dates. 112,650 rows were kept and
   0 rejected — the checks ran, they just found nothing to reject.
3. **Store — star schema, SQLite.** One fact table (`fact_order_items`,
   one row per item) plus four dimensions. Customers are counted by
   `customer_unique_id`, never by `customer_id` — the raw id is near-unique
   per order and would falsely show zero repeat buyers.
4. **Analyse — SQL query pack.** Sixteen numbered queries answer the three
   business questions (revenue leak, cohorts, RFM & churn). Every headline
   number was reconciled three ways (published number = independent SQL
   re-derivation = pure-Python recompute from the raw CSVs), and the
   restatement in `sql/14` excludes cancelled + unavailable orders, so the
   headline revenue (BRL 13,494,400.74) is what the business actually earned.
5. **Visualise — Power BI model.** `powerbi/build_model.py` rebuilds the
   model database from the star schema plus an order-status dimension; 12
   DAX measures carry the headlines and one extra measure carries the
   all-status footnote figure. Every measure value is re-checked against
   the model by `src/check_powerbi_model.py`.
6. **Publish — report.** Three pages (Overview, Revenue leak, Cohorts &
   churn) with preview renders in `outputs/`. The `.pbix` itself is not
   built yet — it needs Power BI Desktop on a Windows machine — so the
   published-link slot is honestly empty, not faked.

## What is NOT in the diagram

- **The `.pbix` file.** Shown as a dashed "not yet built" box. No `.pbix`
  exists in this repo; shipping one without Power BI Desktop would be faking it.
- **A live connection or scheduled refresh.** The model is a static SQLite
  import of a frozen historical extract (it ends Aug 2018). There is nothing
  to refresh and no gateway — the publish guide says so explicitly.
- **The executive summary and recommendations.** They are outputs of layer 4
  (`analysis/executive_summary.md`, `analysis/recommendations.md`), not
  pipeline steps, so they are not nodes — the diagram shows how the numbers
  were produced, not every document that quotes them.
- **The raw CSVs themselves.** They live in `data/raw/` as local build input
  only and are not redistributed from the repo (the Olist repo carries no
  licence file). The repo ships the loader, the schema and the SQLite star.
- **PostgreSQL.** PLAN.md originally sketched PostgreSQL; the build as
  delivered runs on SQLite (`data/processed/f1.db`). The diagram shows what
  was actually built.
- **Two honest limits of the Power BI model.** Churn Rate is a verified
  constant (0.6999) in DAX, not a live calculation, and the cohort matrix is
  a pasted table from `sql/02` — Power BI has no native cohort matrix. Both
  are documented in `powerbi/build-guide.md` §5.

## How to re-render

```bash
npx -y @mermaid-js/mermaid-cli -i docs/architecture.mmd \
  -o outputs/architecture_diagram.png -b white \
  --configFile docs/mmdc-config.json \
  --puppeteerConfigFile /tmp/mmdc-puppeteer.json -s 1.5
```

(The puppeteer config only adds `--no-sandbox`, needed because this VM
runs as root. GitHub renders the `.mmd` file natively, so the PNG is a
preview — the `.mmd` is the source of truth.)
