#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase D November 2016 gap check (11 Nov 2026).

Two independent paths, both from the raw Olist CSVs and the star
schema, never from each other's output:

  (a) SQL: `sql/15_nov2016_gap_check.sql`, run against the live
      database opened READ-ONLY.
  (b) Pure Python: the same monthly numbers recomputed straight
      from the raw CSVs — no database, no ingest script, no SQL file.

Each check compares the SQL result against the Python recompute,
so a mistake in either path shows up as a failure. The headline
question: is November 2016 missing from our load, or from Olist
itself? Answer: from Olist — the raw orders file holds zero
orders with a November 2016 purchase timestamp.

    python3 src/check_nov2016_gap.py [--db data/processed/f1.db]

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
SQL_15 = PROJECT / "sql" / "15_nov2016_gap_check.sql"

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
    """Raw Olist files: order month, order items, customer map."""
    order_month = {}
    with open(RAW / "olist_orders_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            order_month[r["order_id"]] = r["order_purchase_timestamp"][:7]
            order_month[r["order_id"] + "|date"] = \
                r["order_purchase_timestamp"][:10]
    cust_unique = {}
    with open(RAW / "olist_customers_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cust_unique[r["customer_id"]] = r["customer_unique_id"]
    order_customer = {}
    with open(RAW / "olist_orders_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            order_customer[r["order_id"]] = r["customer_id"]
    items = []
    with open(RAW / "olist_order_items_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            items.append((r["order_id"], float(r["price"])))
    return order_month, cust_unique, order_customer, items


def python_recompute(raw):
    """Monthly orders / items / revenue straight from the raw CSVs."""
    order_month, cust_unique, order_customer, items = raw
    monthly = defaultdict(lambda: {"orders": set(), "items": 0,
                                   "revenue": 0.0, "customers": set()})
    for oid, price in items:
        m = order_month[oid]
        monthly[m]["orders"].add(oid)
        monthly[m]["items"] += 1
        monthly[m]["revenue"] += price
        monthly[m]["customers"].add(cust_unique[order_customer[oid]])
    raw_orders = defaultdict(int)
    for oid, m in order_month.items():
        if not oid.endswith("|date"):
            raw_orders[m] += 1
    # First-purchase month per unique customer (cohorts), raw side.
    firstd = {}
    for oid, _ in items:
        uid = cust_unique[order_customer[oid]]
        d = order_month[oid + "|date"]
        if uid not in firstd or d < firstd[uid]:
            firstd[uid] = d
    cohorts = defaultdict(int)
    for d in firstd.values():
        cohorts[d[:7]] += 1
    # Distinct purchase dates in the raw orders file, 2016.
    raw_dates_2016 = sorted({v for k, v in order_month.items()
                             if k.endswith("|date") and v.startswith("2016-")})
    # Dates with orders but no items anywhere in the dataset
    # (the dim_date rows that carry no fact rows).
    dates_with_orders = {v for k, v in order_month.items()
                         if k.endswith("|date")}
    dates_with_items = {order_month[oid + "|date"] for oid, _ in items}
    itemless_dates = sorted(dates_with_orders - dates_with_items)
    return monthly, raw_orders, cohorts, raw_dates_2016, \
        len(dates_with_orders), itemless_dates


def sql_run(db_path):
    """Run sql/15 against the live db (read-only). Returns name -> rows."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    script = SQL_15.read_text(encoding="utf-8")
    out = defaultdict(list)
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
    monthly, raw_orders, cohorts, raw_dates_2016, n_raw_dates, \
        itemless_dates = python_recompute(raw)

    print("== Python recompute (raw CSVs, no DB) ==")
    for m in ("2016-09", "2016-10", "2016-11", "2016-12", "2017-01"):
        v = monthly.get(m, {"orders": set(), "items": 0, "revenue": 0.0})
        print(f"  {m}: raw orders {raw_orders.get(m, 0):>4}  "
              f"item-bearing {len(v['orders']):>4}  items {v['items']:>4}  "
              f"revenue BRL {v['revenue']:>12,.2f}")

    print("== SQL run (sql/15, read-only db) ==")
    sq = sql_run(args.db)
    q1 = {r[1]: r for r in sq["Q1 monthly"]}
    q2 = {r[1]: r for r in sq["Q2 dim_date"]}
    q3 = {r[1]: r for r in sq["Q3 cohort"]}
    q4 = sq["Q4 2016 total"][0]
    q5 = sq["Q5 spine"][0]

    print("== the headline: November 2016 ==")
    check("RAW orders file: 0 orders purchased in Nov 2016",
          raw_orders.get("2016-11", 0) == 0,
          f"got {raw_orders.get('2016-11', 0)}")
    check("RAW items file: 0 items in Nov 2016",
          monthly.get("2016-11", {"items": 0})["items"] == 0)
    check("STAR fact: no Nov 2016 month row at all",
          "2016-11" not in q1)
    check("STAR dim_date: no Nov 2016 rows at all",
          "2016-11" not in q2)
    check("COHORTS: no 2016-11 cohort (Python recompute)",
          "2016-11" not in cohorts)
    check("COHORTS: no 2016-11 cohort (SQL)",
          "2016-11" not in q3)

    print("== the 2016 neighbours (gap is a fragment, not a cliff) ==")
    check("RAW Sep 2016: 4 orders", raw_orders.get("2016-09") == 4,
          f"got {raw_orders.get('2016-09')}")
    check("RAW Oct 2016: 324 orders", raw_orders.get("2016-10") == 324,
          f"got {raw_orders.get('2016-10')}")
    check("RAW Dec 2016: exactly 1 order", raw_orders.get("2016-12") == 1,
          f"got {raw_orders.get('2016-12')}")
    check("RAW Oct 2016: item-bearing purchases span 2–10 Oct only "
          "(one cancelled, item-less order on 22 Oct)",
          min(d for d in raw_dates_2016 if d.startswith("2016-10"))
          == "2016-10-02"
          and max(d for d in raw_dates_2016 if d.startswith("2016-10"))
          == "2016-10-22",
          f"range {min(d for d in raw_dates_2016 if d.startswith('2016-10'))} "
          f"to {max(d for d in raw_dates_2016 if d.startswith('2016-10'))}")
    check("RAW Dec 2016 single order is 23 Dec 2016",
          [d for d in raw_dates_2016 if d.startswith("2016-12")]
          == ["2016-12-23"],
          f"got {[d for d in raw_dates_2016 if d.startswith('2016-12')]}")

    print("== SQL vs independent Python recompute (monthly) ==")
    for m, exp_items, exp_rev in (("2016-09", 6, 267.36),
                                  ("2016-10", 363, 49507.66),
                                  ("2016-12", 1, 10.90),
                                  ("2017-01", 955, 120312.87)):
        r = q1[m]
        p = monthly[m]
        check(f"Q1 {m}: SQL items {r[3]} = Python {p['items']}, "
              f"revenue BRL {r[4]:,.2f} = Python {p['revenue']:,.2f}",
              r[3] == p["items"] and abs(r[4] - p["revenue"]) < TOL
              and r[3] == exp_items and abs(r[4] - exp_rev) < TOL,
              f"sql={r[2:]} python=({len(p['orders'])}, {p['items']}, "
              f"{p['revenue']:,.2f})")
    check("Q1 2016-10: SQL orders 308 = Python item-bearing orders",
          q1["2016-10"][2] == len(monthly["2016-10"]["orders"]),
          f"sql={q1['2016-10'][2]} python={len(monthly['2016-10']['orders'])}")

    print("== dim_date is a presence spine, not a calendar ==")
    check("Q2 Sep 2016: 4 dates present (4, 5, 13, 15 Sep)",
          q2["2016-09"][2] == 4 and q2["2016-09"][3] == "2016-09-04"
          and q2["2016-09"][4] == "2016-09-15",
          f"got {q2['2016-09'][2:]}")
    check("Q2 Oct 2016: 10 dates present (2–10 Oct + 22 Oct)",
          q2["2016-10"][2] == 10 and q2["2016-10"][3] == "2016-10-02"
          and q2["2016-10"][4] == "2016-10-22",
          f"got {q2['2016-10'][2:]}")
    check("Q2 Dec 2016: 1 date present (23 Dec)",
          q2["2016-12"][2] == 1 and q2["2016-12"][3] == "2016-12-23",
          f"got {q2['2016-12'][2:]}")
    check("Q5: dim_date 634 rows = distinct raw order dates (634), "
          "fact covers 616, 18 item-less dates",
          q5[1] == 634 and q5[2] == 616 and q5[3] == 18
          and n_raw_dates == 634 and len(itemless_dates) == 18,
          f"got dim_date={q5[1:]} raw_dates={n_raw_dates} "
          f"itemless={len(itemless_dates)}")
    check("Q5: all 18 item-less dates are in 2016-09/10 or the Sep–Oct "
          "2018 tail (no hidden hole mid-series)",
          all(d.startswith(("2016-09", "2016-10", "2018-08", "2018-09",
                            "2018-10")) for d in itemless_dates),
          f"got {itemless_dates}")

    print("== cohorts and 2016 totals ==")
    check("Q3 cohorts 2016: Sep 3 / Oct 305 / Dec 1, SQL = Python",
          q3["2016-09"][2] == 3 and q3["2016-10"][2] == 305
          and q3["2016-12"][2] == 1
          and cohorts["2016-09"] == 3 and cohorts["2016-10"] == 305
          and cohorts["2016-12"] == 1,
          f"sql={[(k, v[2]) for k, v in q3.items()]} "
          f"python={[(k, cohorts[k]) for k in sorted(cohorts) if k.startswith('2016-')]}")
    check("23 cohorts in total (SQL Q3 + Python agree on the count)",
          len([k for k in cohorts]) == 23,
          f"python cohorts={len(cohorts)}")
    check("Q4 2016 total: 312 orders / 370 items / BRL 49,785.92 / 309 customers",
          q4[1] == 312 and q4[2] == 370
          and abs(q4[3] - 49785.92) < TOL and q4[4] == 309,
          f"got {q4[1:]}")
    check("2016 revenue is 0.37% of the BRL 13,591,643.70 total",
          abs(49785.92 / 13591643.70 * 100 - 0.37) < 0.01,
          f"{49785.92 / 13591643.70 * 100:.3f}%")
    check("RAW 2016 orders 329 = fact orders 312 + 17 item-less orders",
          sum(raw_orders[m] for m in ("2016-09", "2016-10", "2016-12")) == 329
          and q4[1] == 312,
          f"raw={sum(raw_orders[m] for m in ('2016-09', '2016-10', '2016-12'))} fact={q4[1]}")

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
