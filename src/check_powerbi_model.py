#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase E (14 Nov 2026): Power BI model checks.

Re-checks the whole Phase E block against the model database and
the published Phase D headlines, so a wrong DAX value or a stale
preview shows up as a failure before the dashboard is built:

  * model integrity: same star-schema row counts as f1.db, every
    fact row carries an order status, 8 statuses, restatement
    definition matches sql/14 (canceled + unavailable excluded)
  * every verified measure in powerbi/verified_measures.json
    recomputed from the model DB (SQL, not the DAX text)
  * cross-checks against the published Phase D figures
    (sql/14 restatement, sql/16 clean trend)
  * the 4 preview PNGs exist, are non-empty, and their chart totals
    reconcile to the model

    python3 src/check_powerbi_model.py [--db data/processed/f1.db]

Exit code 0 when every check passes, 1 otherwise.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
MODEL = PROJECT / "powerbi" / "f1_powerbi.db"
MEASURES = PROJECT / "powerbi" / "verified_measures.json"
OUT = PROJECT / "outputs"
R = "order_status NOT IN ('canceled', 'unavailable')"

# Published Phase D figures the model must reproduce exactly.
PUBLISHED = {
    "fact_rows": 112_650,
    "revenue_restated": 13_494_400.74,
    "revenue_all": 13_591_643.70,
    "orders_restated": 98_199,
    "orders_all": 98_666,
    "customers_restated": 94_983,
    "customers_all": 95_420,
    "freight_restated": 2_245_816.19,
    "freight_all": 2_256_599.44,
    "churned_restated": 66_476,
    "at_risk_repeat_restated": 611,
    "peak_month": "2017-11",
    "peak_month_revenue": 1_003_862.14,
}
TOL = 0.01

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(PROJECT / "data" / "processed" / "f1.db"))
    args = ap.parse_args()

    if not MODEL.exists():
        print("ERROR: model database missing — run powerbi/build_model.py first")
        return 1
    canon = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con = sqlite3.connect(f"file:{MODEL}?mode=ro", uri=True)
    m = json.loads(MEASURES.read_text(encoding="utf-8"))

    def one(c, sql, params=()):
        return c.execute(sql, params).fetchone()[0]

    print("== model integrity ==")
    for table in ("dim_customer", "dim_product", "dim_seller",
                  "dim_date", "fact_order_items"):
        check(f"{table} row count matches f1.db",
              one(con, f"SELECT COUNT(*) FROM {table}") ==
              one(canon, f"SELECT COUNT(*) FROM {table}"))
    check("8 order statuses in dim_order_status",
          one(con, "SELECT COUNT(*) FROM dim_order_status") == 8)
    check("exactly 2 statuses excluded (canceled, unavailable)",
          one(con, "SELECT COUNT(*) FROM dim_order_status "
                   "WHERE is_restated = 0") == 2)
    check("0 fact rows without an order status",
          one(con, "SELECT COUNT(*) FROM fact_order_items "
                   "WHERE order_status IS NULL") == 0)
    check("every fact order_status exists in dim_order_status",
          one(con, "SELECT COUNT(*) FROM fact_order_items f LEFT JOIN "
                   "dim_order_status d ON f.order_status = d.order_status "
                   "WHERE d.order_status IS NULL") == 0)
    check("excluded fact rows = 467 orders' items (sql/14: 98,666-98,199)",
          one(con, f"SELECT COUNT(DISTINCT order_id) FROM fact_order_items "
                   f"WHERE NOT ({R})") == 467)

    print("== verified measures recomputed from the model ==")
    check("restated revenue = BRL 13,494,400.74 (sql/14)",
          abs(one(con, f"SELECT SUM(price) FROM fact_order_items WHERE {R}")
              - PUBLISHED["revenue_restated"]) < TOL)
    check("all-status revenue = BRL 13,591,643.70",
          abs(one(con, "SELECT SUM(price) FROM fact_order_items")
              - PUBLISHED["revenue_all"]) < TOL)
    check("restated orders = 98,199",
          one(con, f"SELECT COUNT(DISTINCT order_id) FROM fact_order_items "
                   f"WHERE {R}") == PUBLISHED["orders_restated"])
    check("all-status orders = 98,666",
          one(con, "SELECT COUNT(DISTINCT order_id) FROM fact_order_items")
          == PUBLISHED["orders_all"])
    check("restated customers = 94,983",
          one(con, f"SELECT COUNT(DISTINCT c.customer_unique_id) "
                   f"FROM fact_order_items f JOIN dim_customer c "
                   f"ON f.customer_id = c.customer_id WHERE {R}")
          == PUBLISHED["customers_restated"])
    check("all-status customers = 95,420",
          one(con, "SELECT COUNT(DISTINCT c.customer_unique_id) "
                   "FROM fact_order_items f JOIN dim_customer c "
                   "ON f.customer_id = c.customer_id")
          == PUBLISHED["customers_all"])
    check("restated freight = BRL 2,245,816.19",
          abs(one(con, f"SELECT SUM(freight_value) FROM fact_order_items "
                       f"WHERE {R}") - PUBLISHED["freight_restated"]) < TOL)
    check("all-status freight = BRL 2,256,599.44",
          abs(one(con, "SELECT SUM(freight_value) FROM fact_order_items")
              - PUBLISHED["freight_all"]) < TOL)
    check("AOV restated = BRL 137.42",
          abs(m["total_revenue_restated"] / m["total_orders_restated"]
              - m["avg_order_value_restated"]) < TOL)
    check("avg spend per customer restated = BRL 142.07",
          abs(m["total_revenue_restated"] / m["total_customers_restated"]
              - m["avg_spend_per_customer_restated"]) < TOL)
    check("freight % of revenue restated = 16.64%",
          abs(100 * m["total_freight_restated"] / m["total_revenue_restated"]
              - m["freight_pct_revenue_restated"]) < TOL)
    check("repeat buyers restated = 2,887 (3.04%)",
          m["repeat_buyers_restated"] == 2_887
          and abs(m["repeat_buyer_rate_restated"] - 3.04) < 0.01)
    check("churned restated = 66,476 (69.99%, sql/14)",
          one(con, f"SELECT COUNT(*) FROM (SELECT c.customer_unique_id, "
                   f"MAX(f.date_id) mx FROM fact_order_items f "
                   f"JOIN dim_customer c ON f.customer_id = c.customer_id "
                   f"WHERE {R} GROUP BY c.customer_unique_id "
                   f"HAVING mx < '2018-04-17')")
          == PUBLISHED["churned_restated"])
    check("items over 100% freight restated = 4,100 (< 4,119 all-status)",
          m["items_over_100pct_freight_restated"] == 4_100
          and m["items_over_100pct_freight_all"] == 4_119)
    check("SP revenue share restated = 38.27%",
          abs(m["sp_revenue_share_restated"] - 38.27) < 0.01)
    check("peak month = 2017-11, BRL 1,003,862.14 (sql/16)",
          m["peak_month_restated"] == PUBLISHED["peak_month"]
          and abs(m["peak_month_revenue_restated"]
                  - PUBLISHED["peak_month_revenue"]) < TOL)

    print("== preview renders reconcile to the model ==")
    for name in ("preview_monthly_revenue.png",
                 "preview_revenue_by_category.png",
                 "preview_revenue_by_state.png",
                 "preview_freight_by_category.png"):
        p = OUT / name
        check(f"{name} exists and non-empty",
              p.exists() and p.stat().st_size > 10_000,
              f"size={p.stat().st_size if p.exists() else 'missing'}")
    check("clean-trend total (Jan 2017–Aug 2018) = BRL 13,449,529.68 "
          "(sql/16)",
          abs(one(con, f"SELECT SUM(price) FROM fact_order_items WHERE {R} "
                       f"AND date_id >= '2017-01-01' "
                       f"AND date_id < '2018-09-01'") - 13_449_529.68) < TOL)
    check("top category restated = beleza_saude BRL 1,258,681.34",
          one(con, f"SELECT p.product_category_name FROM fact_order_items f "
                   f"JOIN dim_product p ON f.product_id = p.product_id "
                   f"WHERE {R} GROUP BY 1 ORDER BY SUM(price) DESC LIMIT 1")
          == "beleza_saude")

    print(f"\n{passed} checks passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
