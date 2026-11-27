# Flagship 1 — data note (updated 2 Nov 2026: real Olist load)

## Dataset (downloaded and loaded, not planned)

Olist Brazilian e-commerce — public dataset, multi-table
(orders, order items, products, customers, sellers, payments, reviews).
Downloaded 2 Nov 2026 from the official Olist repository
`olist/work-at-olist-data`, directory `datasets/`, branch `master`
(the same files as the Kaggle "Brazilian E-Commerce Public Dataset
by Olist"). Loader: `src/ingest.py`; downloader: `src/download_olist.py`
(header-checked per file). Raw CSVs live in `data/raw/` as local
build input only; the repo ships the loader, the schema and the
SQLite star (`data/processed/f1.db`), not the raw files.

Licence note: the Olist repo README carries no licence file, so the
raw CSVs are NOT redistributed from this repo. Check the Kaggle
dataset page's licence before sharing raw data anywhere; this
project's analysis and derived tables carry attribution to Olist.

## Why this dataset

It is the multi-table, real-mess shape the flagship needs: real joins
(customer → order → item → product/seller), real missing and messy
values, and a size where a star schema and DQ checks actually matter —
unlike a clean single CSV.

## Schema

`../sql/schema.sql` — star schema: `fact_order_items` (item grain) +
`dim_customer` / `dim_product` / `dim_seller` / `dim_date`. Cohort and
RFM analysis keys off `dim_customer.customer_unique_id` (repeat buyers).

## Real load — verified 2 Nov 2026

`python3 src/ingest.py --source-dir data/raw --db data/processed/f1.db`

| Table | Rows |
|---|---|
| dim_customer | 99,441 |
| dim_product | 32,951 |
| dim_seller | 3,095 |
| dim_date | 634 (2016-09-04 → 2018-10-17) |
| fact_order_items | 112,650 (kept), 0 rejected |

Cross-checks (SQLite, same day): total item revenue BRL 13,591,643.70;
distinct orders in fact 98,666; orphan fact rows 0; repeat buyers
(unique customer ids with >1 order) 2,913; top category
beleza_saude BRL 1,258,681.34; 1,603 items sit on products with no
category name (real Olist gap, kept as-is, not patched).

The 1 Nov synthetic-fixture test numbers are superseded by this load.
No fallback dataset was needed — Olist fetched clean on the first
working mirror (the first mirror tried, a student repo, held only
the customers file, so it was abandoned and the official repo used).

## Next steps (toward Fri 27 Nov 2026)

Revenue / cohort / churn analysis queries build on this star in the
week of 9 Nov; nothing analytical is claimed yet — this step is
ingest + verification only.
