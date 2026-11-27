#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase D clean 2017-2018 trend checks (12 Nov 2026).

Two independent paths, both from the raw Olist CSVs and the star
schema, never from each other's output:

  (a) SQL: `sql/16_clean_trend_2017_2018.sql`, run against the live
      database opened READ-ONLY, with order status loaded from
      `data/raw/olist_orders_dataset.csv` into a TEMP staging table
      (the live database is never written to) — same pattern as
      src/check_order_status.py.
  (b) Pure Python: the same monthly numbers recomputed straight from
      the raw CSVs — no database, no ingest script, no SQL file.

Each check compares the SQL result against the Python recompute and
against the published restated headline (10 Nov 2026: revenue excl.
cancelled + unavailable BRL 13,494,400.74, 98,199 orders), so a
mistake in either path shows up as a failure.

    python3 src/check_clean_trend.py [--db data/processed/f1.db]

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
SQL_16 = PROJECT / "sql" / "16_clean_trend_2017_2018.sql"

EXCLUDED = ("canceled", "unavailable")
RESTATED_REVENUE = 13_494_400.74
RESTATED_ORDERS = 98_199
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
    """Order status + purchase month + items, straight from the CSVs."""
    order_status, order_month = {}, {}
    with open(RAW / "olist_orders_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            order_status[r["order_id"]] = r["order_status"]
            order_month[r["order_id"]] = \
                r["order_purchase_timestamp"][:7]  # yyyy-mm
    items = []
    with open(RAW / "olist_order_items_dataset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            items.append((r["order_id"], float(r["price"]),
                          float(r["freight_value"])))
    return order_status, order_month, items


def python_monthly(raw):
    """(year, month) -> {orders, items, revenue, freight}, restated."""
    order_status, order_month, items = raw
    months = defaultdict(lambda: {"orders": set(), "items": 0,
                                  "revenue": 0.0, "freight": 0.0})
    for oid, price, fr in items:
        if order_status[oid] in EXCLUDED:
            continue
        ym = order_month[oid]
        y, m = int(ym[:4]), int(ym[5:7])
        cell = months[(y, m)]
        cell["orders"].add(oid)
        cell["items"] += 1
        cell["revenue"] += price
        cell["freight"] += fr
    return {k: {"orders": len(v["orders"]), "items": v["items"],
                "revenue": round(v["revenue"], 2),
                "freight": round(v["freight"], 2)}
            for k, v in months.items()}


def run_sql(db_path):
    """Run sql/16 against the live DB (read-only) + TEMP staging."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.execute("CREATE TEMP TABLE stg_order_status "
                "(order_id TEXT, order_status TEXT)")
    with open(RAW / "olist_orders_dataset.csv", encoding="utf-8") as f:
        con.executemany(
            "INSERT INTO stg_order_status VALUES (?, ?)",
            [(r["order_id"], r["order_status"]) for r in csv.DictReader(f)])
    sql = SQL_16.read_text()
    # Split on the query markers: Q0, Q1, Q2, Q3. The text before the
    # first marker is the file header — skip it, it is comments only.
    parts = sql.split("-- Q")[1:]
    results = {}
    for part in parts:
        label = part.split("\n", 1)[0].strip()[0]  # '0'..'3'
        stmt = "-- Q" + part
        rows = con.execute(stmt).fetchall()
        results["Q" + label] = rows
    con.close()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(PROJECT / "data" / "processed"
                                        / "f1.db"))
    args = ap.parse_args()

    raw = load_raw()
    monthly = python_monthly(raw)
    sql = run_sql(args.db)

    # ── Q0 staging guard ─────────────────────────────────────────────
    q0 = sql["Q0"][0]
    check("Q0 staging: 99,441 status rows", q0[1] == 99441, str(q0[1]))
    check("Q0 staging: 8 distinct statuses", q0[2] == 8, str(q0[2]))
    check("Q0 staging: 0 fact rows without a status", q0[3] == 0,
          str(q0[3]))

    # ── Q1 clean trend: 20 months, Jan 2017 → Aug 2018 ──────────────
    q1 = sql["Q1"]
    check("Q1 returns exactly 20 months", len(q1) == 20, str(len(q1)))
    check("Q1 starts Jan 2017", (q1[0][0], q1[0][1]) == (2017, 1),
          str(q1[0][:2]))
    check("Q1 ends Aug 2018 (Sep 2018 is a 1-order stub, not trend)",
          (q1[-1][0], q1[-1][1]) == (2018, 8), str(q1[-1][:2]))
    check("Q1 months are consecutive (no hidden gaps)",
          [(r[0], r[1]) for r in q1] ==
          [(y, m) for y in (2017, 2018) for m in range(1, 13)
           if not (y == 2018 and m > 8)])
    bad = 0
    for r in q1:
        py = monthly[(r[0], r[1])]
        if not (r[2] == py["orders"] and r[3] == py["items"]
                and abs(r[4] - py["revenue"]) <= TOL
                and abs(r[5] - py["freight"]) <= TOL
                and abs(r[6] - round(py["revenue"] / py["orders"], 2))
                <= TOL):
            bad += 1
            print(f"    mismatch {r[0]}-{r[1]:02d}: sql={r[2:7]} "
                  f"python={py}")
    check("Q1 every month matches the Python recompute", bad == 0,
          f"{bad} mismatches")
    # MoM / YoY / cumulative, checked from the Python monthly table
    revs = [monthly[(r[0], r[1])]["revenue"] for r in q1]
    mom_bad = yoy_bad = cum_bad = 0
    for i, r in enumerate(q1):
        mom = None if i == 0 else round(100 * (revs[i] - revs[i - 1])
                                        / revs[i - 1], 2)
        yoy = None if i < 12 else round(100 * (revs[i] - revs[i - 12])
                                        / revs[i - 12], 2)
        cum = round(sum(revs[:i + 1]), 2)
        if (r[7] is None) != (mom is None) or (
                mom is not None and abs(r[7] - mom) > TOL):
            mom_bad += 1
        if (r[8] is None) != (yoy is None) or (
                yoy is not None and abs(r[8] - yoy) > TOL):
            yoy_bad += 1
        if abs(r[9] - cum) > TOL:
            cum_bad += 1
    check("Q1 MoM growth matches recompute", mom_bad == 0,
          f"{mom_bad} mismatches")
    check("Q1 YoY growth matches recompute (Jan 2018 onward)",
          yoy_bad == 0, f"{yoy_bad} mismatches")
    check("Q1 YoY is NULL for all of 2017",
          all(r[8] is None for r in q1[:12]))
    check("Q1 cumulative revenue matches recompute", cum_bad == 0,
          f"{cum_bad} mismatches")

    # ── The clean window must reconcile to the restated headline ────
    clean_rev = round(sum(revs), 2)
    stub_2016 = {k: v for k, v in monthly.items() if k[0] == 2016}
    stub_2018 = {k: v for k, v in monthly.items()
                 if k == (2018, 9)}
    stub_rev = round(sum(v["revenue"] for v in stub_2016.values())
                     + sum(v["revenue"] for v in stub_2018.values()), 2)
    check("clean window + stubs = restated revenue",
          abs(clean_rev + stub_rev - RESTATED_REVENUE) <= TOL,
          f"clean {clean_rev:,} + stubs {stub_rev:,} = "
          f"{clean_rev + stub_rev:,} vs {RESTATED_REVENUE:,}")
    clean_orders = sum(monthly[(r[0], r[1])]["orders"] for r in q1)
    stub_orders = (sum(v["orders"] for v in stub_2016.values())
                   + sum(v["orders"] for v in stub_2018.values()))
    check("clean window + stubs = restated orders",
          clean_orders + stub_orders == RESTATED_ORDERS,
          f"{clean_orders} + {stub_orders} = "
          f"{clean_orders + stub_orders} vs {RESTATED_ORDERS}")
    check("Sep 2018 stub is exactly 1 order, BRL 145.00",
          stub_2018.get((2018, 9), {}).get("orders") == 1
          and abs(stub_2018[(2018, 9)]["revenue"] - 145.00) <= TOL,
          str(stub_2018.get((2018, 9))))

    # ── Q2 stubs ─────────────────────────────────────────────────────
    q2 = sql["Q2"]
    check("Q2 returns 4 rows (Sep/Oct/Dec 2016 + Sep 2018)",
          len(q2) == 4, str(len(q2)))
    check("Q2 has no November 2016 row",
          all(not (r[0] == 2016 and r[1] == 11) for r in q2))
    check("Q2 has no October 2018 row (all 4 orders cancelled)",
          all(not (r[0] == 2018 and r[1] == 10) for r in q2))
    check("Q2 Sep 2018 row = 1 order, BRL 145.00",
          any(r[0] == 2018 and r[1] == 9 and r[2] == 1
              and abs(r[4] - 145.00) <= TOL for r in q2))
    q2_bad = 0
    for r in q2:
        py = monthly[(r[0], r[1])]
        if not (r[2] == py["orders"] and r[3] == py["items"]
                and abs(r[4] - py["revenue"]) <= TOL):
            q2_bad += 1
    check("Q2 stub months match the Python recompute", q2_bad == 0,
          f"{q2_bad} mismatches")

    # ── Q3 half years ────────────────────────────────────────────────
    q3 = sql["Q3"][0]
    h1_17 = round(sum(monthly[(2017, m)]["revenue"] for m in range(1, 7)), 2)
    h1_18 = round(sum(monthly[(2018, m)]["revenue"] for m in range(1, 7)), 2)
    check("Q3 H1 2017 matches recompute", abs(q3[1] - h1_17) <= TOL,
          f"sql {q3[1]} vs {h1_17}")
    check("Q3 H1 2018 matches recompute", abs(q3[2] - h1_18) <= TOL,
          f"sql {q3[2]} vs {h1_18}")
    check("Q3 H1 growth matches recompute",
          abs(q3[3] - round(100 * (h1_18 - h1_17) / h1_17, 2)) <= TOL,
          f"sql {q3[3]}")
    check("Q3 2017 total matches recompute",
          abs(q3[4] - round(sum(monthly[(2017, m)]["revenue"]
                                  for m in range(1, 13)), 2)) <= TOL)
    check("Q3 2018 Jan-Aug total matches clean window",
          abs(q3[5] - round(sum(revs[12:]), 2)) <= TOL)

    print(f"\n{passed}/{passed + failed} checks passed")
    if failed:
        print("FAILURES:", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
