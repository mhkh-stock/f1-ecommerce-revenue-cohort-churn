#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase D order-status restatement checks (10 Nov 2026).

Two independent paths, both from the raw Olist CSVs and the star
schema, never from each other's output:

  (a) SQL: `sql/14_order_status_restatement.sql`, run against the
      live database opened READ-ONLY, with order status loaded from
      `data/raw/olist_orders_dataset.csv` into a TEMP staging table
      (the live database is never written to).
  (b) Pure Python: the same headlines recomputed straight from the
      raw CSVs — no database, no ingest script, no SQL file.

Each check compares the SQL result against the Python recompute and
against the published all-status Phase B/C headlines, so a mistake
in either path shows up as a failure.

    python3 src/check_order_status.py [--db data/processed/f1.db]

Exit code 0 when every check passes, 1 otherwise.
"""
import argparse
import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
SQL_14 = PROJECT / "sql" / "14_order_status_restatement.sql"

# Published all-status Phase B/C headlines (the numbers under test).
PUBLISHED = {
    "fact_rows": 112_650,
    "orders": 98_666,
    "revenue": 13_591_643.70,
    "freight": 2_256_599.44,
    "customers": 95_420,
    "repeat_buyers": 2_913,
    "avg_spend": 142.44,
    "churned": 66_802,
    "active": 28_618,
    "at_risk": 18_594,
    "at_risk_revenue": 2_751_210.98,
    "at_risk_repeat": 617,
    "at_risk_repeat_revenue": 169_495.02,
}
EXCLUDED = ("canceled", "unavailable")
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


def load_raw():
    """Raw Olist files, read once and shared by both paths."""
    cust_unique = {}
    with open(RAW / "olist_customers_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cust_unique[r["customer_id"]] = r["customer_unique_id"]
    order_status, order_customer, order_date = {}, {}, {}
    with open(RAW / "olist_orders_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            order_status[r["order_id"]] = r["order_status"]
            order_customer[r["order_id"]] = r["customer_id"]
            order_date[r["order_id"]] = r["order_purchase_timestamp"][:10]
    items = []
    with open(RAW / "olist_order_items_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            items.append((r["order_id"], float(r["price"]),
                          float(r["freight_value"])))
    return cust_unique, order_status, order_customer, order_date, items


def python_recompute(raw, keep):
    """Headlines straight from the raw CSVs, under one status filter.

    keep(status) -> True for orders that count. No database involved.
    """
    cust_unique, order_status, order_customer, order_date, items = raw
    revenue = freight = 0.0
    orders_with_items = set()
    last_purchase = {}
    orders_per_unique = defaultdict(set)
    spend_per_unique = defaultdict(float)
    for oid, price, fr in items:
        if not keep(order_status[oid]):
            continue
        revenue += price
        freight += fr
        orders_with_items.add(oid)
        uid = cust_unique[order_customer[oid]]
        d = order_date[oid]
        if uid not in last_purchase or d > last_purchase[uid]:
            last_purchase[uid] = d
        orders_per_unique[uid].add(oid)
        spend_per_unique[uid] += price
    churned = sum(1 for d in last_purchase.values() if d < "2018-04-17")
    active = sum(1 for d in last_purchase.values() if d >= "2018-04-17")
    at_risk = [u for u, d in last_purchase.items()
               if "2018-04-17" <= d < "2018-07-17"]
    at_risk_rep = [u for u in at_risk if len(orders_per_unique[u]) > 1]
    return {
        "fact_rows": sum(1 for oid, _, _ in items
                         if keep(order_status[oid])),
        "orders": len(orders_with_items),
        "revenue": round(revenue, 2),
        "freight": round(freight, 2),
        "customers": len(last_purchase),
        "repeat_buyers": sum(1 for v in orders_per_unique.values()
                             if len(v) > 1),
        "avg_spend": round(revenue / len(last_purchase), 2),
        "churned": churned,
        "active": active,
        "at_risk": len(at_risk),
        "at_risk_revenue": round(sum(spend_per_unique[u]
                                     for u in at_risk), 2),
        "at_risk_repeat": len(at_risk_rep),
        "at_risk_repeat_revenue": round(sum(spend_per_unique[u]
                                            for u in at_risk_rep), 2),
    }


def sql_run(db_path, raw):
    """Run sql/14 against the live db (read-only) with a TEMP staging
    table loaded from the raw orders CSV. Returns check_name -> rows."""
    _, order_status, _, _, _ = raw
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.execute("CREATE TEMP TABLE stg_order_status "
                "(order_id TEXT PRIMARY KEY, order_status TEXT NOT NULL)")
    con.executemany("INSERT INTO stg_order_status VALUES (?, ?)",
                    order_status.items())
    script = SQL_14.read_text(encoding="utf-8")
    out = defaultdict(list)
    # Statements are separated by ";\n"; comments carry no semicolons.
    statements = [s.strip() for s in script.split(";\n")]
    for stmt in statements:
        if not stmt:
            continue
        lines = [ln for ln in stmt.splitlines()
                 if not ln.strip().startswith("--")]
        q = "\n".join(lines).strip()
        if not q:
            continue
        for row in con.execute(q):
            out[row[0]].append(row)
    con.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(PROJECT / "data" / "processed" / "f1.db"))
    args = ap.parse_args()

    raw = load_raw()
    _, order_status, _, _, _ = raw

    print("== Python recompute (raw CSVs, no DB) ==")
    py_all = python_recompute(raw, lambda s: True)
    py_rest = python_recompute(raw, lambda s: s not in EXCLUDED)
    py_del = python_recompute(raw, lambda s: s == "delivered")
    print(f"  all-status revenue BRL {py_all['revenue']:,.2f}, "
          f"restated BRL {py_rest['revenue']:,.2f}, "
          f"delivered-only BRL {py_del['revenue']:,.2f}")

    print("== SQL run (sql/14, read-only db + temp staging) ==")
    sq = sql_run(args.db, raw)
    q0 = sq["Q0 staging"][0]
    q1 = sq["Q1 by status"]
    q1b = sq["Q1b no items"]
    q2 = sq["Q2 restated"][0]
    q3 = sq["Q3 delivered-only"][0]
    q4a = sq["Q4a delta restated"][0]
    q4b = sq["Q4b delta delivered-only"][0]
    q5 = sq["Q5 churn restated"][0]
    q6 = sq["Q6 churn delivered-only"][0]
    q7 = sq["Q7 at-risk restated"][0]

    by_status = {row[1]: row for row in q1}
    excluded_rev = round(sum(by_status[s][4] for s in EXCLUDED), 2)
    excluded_rows = sum(by_status[s][3] for s in EXCLUDED)
    excluded_orders = sum(by_status[s][2] for s in EXCLUDED)

    print("== staging and completeness ==")
    check("Q0: 99,441 status rows loaded", q0[1] == 99_441,
          f"got {q0[1]}")
    check("Q0: 8 distinct order statuses", q0[2] == 8, f"got {q0[2]}")
    check("Q0: 0 fact rows orphaned (no status)", q0[3] == 0,
          f"got {q0[3]}")
    check("Q1: per-status orders sum to 98,666",
          sum(r[2] for r in q1) == 98_666,
          f"got {sum(r[2] for r in q1)}")
    check("Q1: per-status fact rows sum to 112,650",
          sum(r[3] for r in q1) == 112_650,
          f"got {sum(r[3] for r in q1)}")
    check("Q1: per-status revenue sums to BRL 13,591,643.70",
          abs(sum(r[4] for r in q1) - PUBLISHED["revenue"]) < TOL,
          f"got {sum(r[4] for r in q1):,.2f}")
    check("Q1: per-status freight sums to BRL 2,256,599.44",
          abs(sum(r[5] for r in q1) - PUBLISHED["freight"]) < TOL,
          f"got {sum(r[5] for r in q1):,.2f}")
    check("Q1b: orders with no items sum to 775 (99,441 - 98,666)",
          sum(r[2] for r in q1b) == 775,
          f"got {sum(r[2] for r in q1b)}")

    print("== restatement arithmetic (SQL only) ==")
    check("restated revenue + excluded revenue = published, to the cent",
          abs(q2[3] + excluded_rev - PUBLISHED["revenue"]) < TOL,
          f"{q2[3]:,.2f} + {excluded_rev:,.2f} != {PUBLISHED['revenue']:,.2f}")
    check("restated fact rows + excluded fact rows = 112,650",
          q2[2] + excluded_rows == 112_650,
          f"{q2[2]} + {excluded_rows}")
    check("restated orders + excluded orders = 98,666",
          q2[1] + excluded_orders == 98_666,
          f"{q2[1]} + {excluded_orders}")
    check("delivered-only revenue <= restated revenue",
          q3[3] <= q2[3], f"delivered {q3[3]:,.2f} > restated {q2[3]:,.2f}")
    check("restated customers (94,983) <= published 95,420",
          q2[5] <= PUBLISHED["customers"], f"got {q2[5]}")
    check("Q4a: restated revenue delta is -BRL 97,242.96",
          abs(q4a[3] - (-97_242.96)) < TOL, f"got {q4a[3]:,.2f}")
    check("Q4b: delivered-only revenue delta is -BRL 370,145.59",
          abs(q4b[3] - (-370_145.59)) < TOL, f"got {q4b[3]:,.2f}")

    print("== cancelled + unavailable share, re-derived not copied ==")
    n_excl_raw = sum(1 for s in order_status.values() if s in EXCLUDED)
    share_raw = 100.0 * n_excl_raw / len(order_status)
    check("cancelled+unavailable = 1.24% of all 99,441 raw orders",
          abs(share_raw - 1.24) < 0.01,
          f"{n_excl_raw}/{len(order_status)} = {share_raw:.3f}%")
    check("...but only 0.47% of item-bearing orders (467 of 98,666)",
          abs(100.0 * excluded_orders / 98_666 - 0.47) < 0.01,
          f"{excluded_orders}/98,666 = {100.0 * excluded_orders / 98_666:.3f}%")

    print("== SQL vs independent Python recompute ==")
    for key, idx in (("orders", 1), ("fact_rows", 2), ("revenue", 3),
                     ("freight", 4), ("customers", 5),
                     ("repeat_buyers", 6), ("avg_spend", 7)):
        check(f"Q2 restated {key}: SQL {q2[idx]:,} = Python {py_rest[key]:,}",
              abs(q2[idx] - py_rest[key]) < TOL,
              f"sql={q2[idx]} python={py_rest[key]}")
    for key, idx in (("orders", 1), ("fact_rows", 2), ("revenue", 3),
                     ("freight", 4), ("customers", 5),
                     ("repeat_buyers", 6), ("avg_spend", 7)):
        check(f"Q3 delivered-only {key}: SQL {q3[idx]:,} = Python {py_del[key]:,}",
              abs(q3[idx] - py_del[key]) < TOL,
              f"sql={q3[idx]} python={py_del[key]}")
    check("Q5 restated churn: SQL = Python (66,476 / 28,507)",
          q5[1] == py_rest["churned"] and q5[2] == py_rest["active"],
          f"sql={q5[1:]}, python=({py_rest['churned']}, {py_rest['active']})")
    check("Q6 delivered-only churn: SQL = Python (65,170 / 28,188)",
          q6[1] == py_del["churned"] and q6[2] == py_del["active"],
          f"sql={q6[1:]}, python=({py_del['churned']}, {py_del['active']})")
    check("Q7 restated at-risk: SQL = Python (18,536 / BRL 2,733,862.67)",
          q7[1] == py_rest["at_risk"]
          and abs(q7[2] - py_rest["at_risk_revenue"]) < TOL,
          f"sql={q7[1:3]}, python=({py_rest['at_risk']}, {py_rest['at_risk_revenue']})")
    check("Q7 restated at-risk repeat buyers: SQL = Python (611 / BRL 168,541.14)",
          q7[3] == py_rest["at_risk_repeat"]
          and abs(q7[4] - py_rest["at_risk_repeat_revenue"]) < TOL,
          f"sql={q7[3:]}, python=({py_rest['at_risk_repeat']}, {py_rest['at_risk_repeat_revenue']})")
    check("Python all-status recompute still matches published headlines",
          py_all["revenue"] == PUBLISHED["revenue"]
          and py_all["orders"] == PUBLISHED["orders"]
          and py_all["customers"] == PUBLISHED["customers"]
          and py_all["at_risk_repeat"] == PUBLISHED["at_risk_repeat"],
          f"python={py_all}")

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
