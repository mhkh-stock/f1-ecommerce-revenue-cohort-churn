#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase E (14 Nov 2026): build the Power BI model database.

The canonical star schema (`data/processed/f1.db`) carries no order
status (PLAN.md gap, decided 4 Nov 2026) — so the dashboard's headline
measures must be the RESTATED ones (excluding cancelled + unavailable
orders, `sql/14`, 36 checks). Rather than rewriting the canonical
database, this script builds a separate, rebuildable model database:

  data/processed/f1.db  (read-only)  +  data/raw/olist_orders_dataset.csv
        ──▶  powerbi/f1_powerbi.db

`f1_powerbi.db` is the same star schema plus:
  * `dim_order_status` — the 8 Olist order statuses
  * `order_status` on `fact_order_items` (every fact row carries one;
    0 orphans — enforced here and checked in src/check_powerbi_model.py)

The restatement itself stays a MEASURE-level filter (see
`powerbi/measures.dax`): the fact table keeps every row, so the
all-status reconciliation footnote (BRL 13,591,643.70) is still
provable from the model, and no revenue is silently deleted.

The model DB is NOT uploaded to GitHub (rebuildable from the pushed
scripts + raw CSVs, same rule as every other .db in this portfolio).

    python3 powerbi/build_model.py [--db data/processed/f1.db]
"""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
POWERBI = PROJECT / "powerbi"
RAW = PROJECT / "data" / "raw"
ORDERS_CSV = RAW / "olist_orders_dataset.csv"

EXCLUDED = ("canceled", "unavailable")  # restatement definition, sql/14


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(PROJECT / "data" / "processed" / "f1.db"))
    args = ap.parse_args()

    src = Path(args.db)
    if not src.exists():
        print(f"ERROR: source database not found: {src}")
        return 1
    if not ORDERS_CSV.exists():
        print(f"ERROR: raw orders file not found: {ORDERS_CSV}")
        return 1

    # Order status per order, straight from the raw Olist orders file.
    status_by_order = {}
    with open(ORDERS_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            status_by_order[row["order_id"]] = row["order_status"]
    print(f"statuses loaded: {len(status_by_order):,} orders, "
          f"{len(set(status_by_order.values()))} distinct statuses")

    POWERBI.mkdir(exist_ok=True)
    out = POWERBI / "f1_powerbi.db"
    if out.exists():
        out.unlink()

    con_in = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    con = sqlite3.connect(out)
    cur = con.cursor()

    # Copy the star schema tables verbatim (structure + rows).
    for table in ("dim_customer", "dim_product", "dim_seller",
                  "dim_date", "fact_order_items"):
        ddl = con_in.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,)).fetchone()[0]
        cur.execute(ddl)
        rows = con_in.execute(f"SELECT * FROM {table}").fetchall()
        cols = [d[0] for d in con_in.execute(
            f"SELECT * FROM {table} LIMIT 0").description]
        cur.executemany(
            f"INSERT INTO {table} ({','.join(cols)}) "
            f"VALUES ({','.join('?' * len(cols))})", rows)
        print(f"copied {table}: {len(rows):,} rows")
    con_in.close()

    # dim_order_status + order_status on the fact table.
    cur.execute(
        "CREATE TABLE dim_order_status ("
        "  order_status TEXT PRIMARY KEY,"
        "  is_restated INTEGER NOT NULL CHECK (is_restated IN (0, 1)),"
        "  status_group TEXT NOT NULL)")
    for status in sorted(set(status_by_order.values())):
        group = ("excluded — cancelled/unavailable" if status in EXCLUDED
                 else "included — revenue earned")
        cur.execute(
            "INSERT INTO dim_order_status VALUES (?, ?, ?)",
            (status, 0 if status in EXCLUDED else 1, group))

    cur.execute("ALTER TABLE fact_order_items ADD COLUMN order_status TEXT")
    cur.execute(
        "CREATE INDEX idx_fact_status ON fact_order_items(order_status)")
    fact_orders = [r[0] for r in cur.execute(
        "SELECT DISTINCT order_id FROM fact_order_items")]
    missing = [o for o in fact_orders if o not in status_by_order]
    if missing:
        print(f"ERROR: {len(missing)} fact orders have no status in the "
              "raw orders file")
        con.close()
        out.unlink()
        return 1
    cur.executemany(
        "UPDATE fact_order_items SET order_status = ? WHERE order_id = ?",
        [(status_by_order[o], o) for o in fact_orders])
    con.commit()

    # Verified headline values, written for the DAX file + checks.
    def one(sql, params=()):
        return cur.execute(sql, params).fetchone()[0]

    restated = "order_status NOT IN ('canceled', 'unavailable')"
    measures = {
        "total_revenue_restated": round(one(
            f"SELECT SUM(price) FROM fact_order_items WHERE {restated}"), 2),
        "total_revenue_all_statuses": round(one(
            "SELECT SUM(price) FROM fact_order_items"), 2),
        "total_orders_restated": one(
            f"SELECT COUNT(DISTINCT order_id) FROM fact_order_items "
            f"WHERE {restated}"),
        "total_orders_all_statuses": one(
            "SELECT COUNT(DISTINCT order_id) FROM fact_order_items"),
        "total_customers_restated": one(
            f"SELECT COUNT(DISTINCT c.customer_unique_id) "
            f"FROM fact_order_items f JOIN dim_customer c "
            f"ON f.customer_id = c.customer_id WHERE {restated}"),
        "total_customers_all_statuses": one(
            "SELECT COUNT(DISTINCT c.customer_unique_id) "
            "FROM fact_order_items f JOIN dim_customer c "
            "ON f.customer_id = c.customer_id"),
        "total_freight_restated": round(one(
            f"SELECT SUM(freight_value) FROM fact_order_items "
            f"WHERE {restated}"), 2),
        "total_freight_all_statuses": round(one(
            "SELECT SUM(freight_value) FROM fact_order_items"), 2),
        "items_over_100pct_freight_restated": one(
            f"SELECT COUNT(*) FROM fact_order_items WHERE {restated} "
            f"AND freight_value > price"),
        "items_over_100pct_freight_all": one(
            "SELECT COUNT(*) FROM fact_order_items "
            "WHERE freight_value > price"),
        "fact_rows": one("SELECT COUNT(*) FROM fact_order_items"),
        "fact_rows_no_status": one(
            "SELECT COUNT(*) FROM fact_order_items WHERE order_status IS NULL"),
        "distinct_statuses": one(
            "SELECT COUNT(*) FROM dim_order_status"),
    }
    measures["avg_order_value_restated"] = round(
        measures["total_revenue_restated"] / measures["total_orders_restated"], 2)
    measures["avg_spend_per_customer_restated"] = round(
        measures["total_revenue_restated"] / measures["total_customers_restated"], 2)
    measures["freight_pct_revenue_restated"] = round(
        100 * measures["total_freight_restated"] / measures["total_revenue_restated"], 2)
    measures["sp_revenue_share_restated"] = round(100 * one(
        f"SELECT SUM(price) FROM fact_order_items f "
        f"JOIN dim_customer c ON f.customer_id = c.customer_id "
        f"WHERE {restated} AND c.customer_state = 'SP'")
        / measures["total_revenue_restated"], 2)
    measures["peak_month_restated"] = one(
        f"SELECT substr(date_id, 1, 7) FROM fact_order_items "
        f"WHERE {restated} GROUP BY 1 ORDER BY SUM(price) DESC LIMIT 1")
    measures["peak_month_revenue_restated"] = round(one(
        f"SELECT SUM(price) FROM fact_order_items WHERE {restated} "
        f"AND substr(date_id, 1, 7) = ?", (measures["peak_month_restated"],)), 2)

    import json
    with open(POWERBI / "verified_measures.json", "w", encoding="utf-8") as f:
        json.dump(measures, f, indent=2, sort_keys=True)
    con.close()

    for k in sorted(measures):
        v = measures[k]
        print(f"  {k}: {v:,}" if isinstance(v, (int, float)) else f"  {k}: {v}")
    print(f"model written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
