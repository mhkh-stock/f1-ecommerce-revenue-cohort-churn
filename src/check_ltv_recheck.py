#!/usr/bin/env python3
"""Phase D per-cohort LTV re-check for Flagship 1 (run: python3 src/check_ltv_recheck.py).

Third path, independent of both SQL files: pure Python straight from
the raw Olist CSVs (no database, no ingest script). Recomputes every
cohort's customers / repeat buyers / revenue / LTV and the Oct–Dec 2017
month-1/2/3 retention, then compares against the published Phase B
numbers (sql/09 output, captured 9 Nov 2026) and the sql/13 recheck
output. Tolerance: BRL 0.01 on money, 0.01pp on percentages.
Exit code 0 = all pass.
"""
import csv
import sqlite3
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "processed" / "f1.db"

# Published Phase B numbers (sql/09 Q1, run 9 Nov 2026): cohort ->
# (customers, repeat_buyers, revenue, ltv). Copied from the sql/09 run
# output so this script can run without re-running sql/09.
PUBLISHED_LTV = {
    "2016-09": (3, 0, 267.36, 89.12), "2016-10": (305, 12, 50955.12, 167.07),
    "2016-12": (1, 1, 21.80, 21.80), "2017-01": (754, 55, 123159.75, 163.34),
    "2017-02": (1705, 70, 252976.22, 148.37), "2017-03": (2595, 129, 387443.32, 149.30),
    "2017-04": (2339, 107, 371657.53, 158.90), "2017-05": (3560, 191, 520261.54, 146.14),
    "2017-06": (3114, 170, 447229.53, 143.62), "2017-07": (3843, 181, 505745.39, 131.60),
    "2017-08": (4149, 194, 584686.14, 140.92), "2017-09": (4090, 189, 630630.91, 154.19),
    "2017-10": (4412, 167, 668103.66, 151.43), "2017-11": (7217, 231, 1014927.64, 140.63),
    "2017-12": (5442, 146, 739625.61, 135.91), "2018-01": (6983, 215, 946709.92, 135.57),
    "2018-02": (6422, 242, 845799.09, 131.70), "2018-03": (6947, 171, 977238.77, 140.67),
    "2018-04": (6709, 132, 983709.10, 146.63), "2018-05": (6604, 114, 982827.40, 148.82),
    "2018-06": (5934, 71, 843333.20, 142.12), "2018-07": (6054, 90, 878678.61, 145.14),
    "2018-08": (6238, 35, 835656.09, 133.96),
}
# Published Phase B retention (sql/09 Q2): cohort -> (m1, m2, m3) in %.
PUBLISHED_RET = {
    "2017-10": (0.70, 0.25, 0.09), "2017-11": (0.55, 0.39, 0.18),
    "2017-12": (0.22, 0.28, 0.35),
}

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def month_add(ym, n):
    y, m = int(ym[:4]), int(ym[5:7])
    m += n
    return f"{y + (m - 1) // 12:04d}-{(m - 1) % 12 + 1:02d}"


def main():
    # --- pure-Python recompute from the raw CSVs ---
    cust_unique = {}  # customer_id -> customer_unique_id
    for r in csv.DictReader(open(RAW / "olist_customers_dataset.csv", encoding="utf-8")):
        cust_unique[r["customer_id"]] = r["customer_unique_id"]
    order_customer = {}  # order_id -> customer_id
    for r in csv.DictReader(open(RAW / "olist_orders_dataset.csv", encoding="utf-8")):
        order_customer[r["order_id"]] = r["customer_id"]
    # item rows: (unique customer, order_id, price)
    first_buy, spend, orders, active = {}, defaultdict(float), defaultdict(set), defaultdict(set)
    for r in csv.DictReader(open(RAW / "olist_order_items_dataset.csv", encoding="utf-8")):
        uid = cust_unique[order_customer[r["order_id"]]]
        spend[uid] += float(r["price"])
        orders[uid].add(r["order_id"])
    # purchase dates come from the orders file, not the items file
    order_date = {r["order_id"]: r["order_purchase_timestamp"][:10]
                  for r in csv.DictReader(open(RAW / "olist_orders_dataset.csv", encoding="utf-8"))}
    for r in csv.DictReader(open(RAW / "olist_order_items_dataset.csv", encoding="utf-8")):
        uid = cust_unique[order_customer[r["order_id"]]]
        d = order_date[r["order_id"]]
        if uid not in first_buy or d < first_buy[uid]:
            first_buy[uid] = d
        active[uid].add(d[:7])

    cohort_of = {u: d[:7] for u, d in first_buy.items()}
    by_cohort = defaultdict(list)
    for u, c in cohort_of.items():
        by_cohort[c].append(u)

    print("== per-cohort LTV: Python recompute vs published Phase B ==")
    all_match = True
    for c in sorted(PUBLISHED_LTV):
        users = by_cohort[c]
        rev = round(sum(spend[u] for u in users), 2)
        rep = sum(1 for u in users if len(orders[u]) > 1)
        ltv = round(rev / len(users), 2)
        exp = PUBLISHED_LTV[c]
        ok = (len(users) == exp[0] and rep == exp[1]
              and abs(rev - exp[2]) < 0.01 and abs(ltv - exp[3]) < 0.01)
        if not ok:
            all_match = False
            print(f"  FAIL  {c}: python ({len(users)}, {rep}, {rev}, {ltv}) "
                  f"vs published {exp}")
        if c in ("2016-09", "2016-12"):
            check(f"tiny cohort {c} matches (read with care, n={exp[0]})", ok)
    check("all 23 cohorts match published LTV (customers, repeat, revenue, LTV)",
          all_match and len(by_cohort) == 23, f"cohorts={len(by_cohort)}")
    check("cohort customers sum to 95,420",
          sum(len(v) for v in by_cohort.values()) == 95420)
    check("cohort revenue sums to BRL 13,591,643.70",
          abs(sum(spend.values()) - 13591643.70) < 0.01, f"got {sum(spend.values()):.2f}")

    print("== retention: Python recompute vs published Phase B ==")
    for c in sorted(PUBLISHED_RET):
        users = set(by_cohort[c])
        got = []
        for n in (1, 2, 3):
            m = month_add(c, n)
            retained = sum(1 for u in users if m in active[u])
            got.append(round(100.0 * retained / len(users), 2))
        exp = PUBLISHED_RET[c]
        check(f"retention {c} m1/m2/m3 {got} vs published {exp}",
              all(abs(g - e) < 0.01 for g, e in zip(got, exp)), f"got {got}")

    print("== flat-LTV claim ==")
    big = {c: (len(v), round(sum(spend[u] for u in v) / len(v), 2))
           for c, v in by_cohort.items() if len(v) > 300}
    lo, hi = min(v[1] for v in big.values()), max(v[1] for v in big.values())
    check("LTV range for cohorts >300 customers is BRL 131–167",
          abs(lo - 131.60) < 0.01 and abs(hi - 167.07) < 0.01, f"got {lo}–{hi}")
    check("overall LTV BRL 142.44",
          abs(sum(spend.values()) / 95420 - 142.44) < 0.01)

    print("== sql/13 recheck output vs published ==")
    out = subprocess.run(["sqlite3", str(DB)],
                         input=open(ROOT / "sql" / "13_cohort_ltv_recheck.sql",
                                    encoding="utf-8").read(),
                         capture_output=True, text=True)
    lines = [l for l in out.stdout.strip().split("\n") if l]
    q1 = [l.split("|") for l in lines[:23]]
    ok13 = all(
        row[0] in PUBLISHED_LTV
        and int(row[1]) == PUBLISHED_LTV[row[0]][0]
        and int(row[2]) == PUBLISHED_LTV[row[0]][1]
        and abs(float(row[5]) - PUBLISHED_LTV[row[0]][2]) < 0.01
        and abs(float(row[6]) - PUBLISHED_LTV[row[0]][3]) < 0.01
        for row in q1)
    check("sql/13 Q1 matches published LTV on all 23 cohorts", ok13)
    q2 = [l.split("|") for l in lines[23:26]]
    ok13r = all(
        row[0] in PUBLISHED_RET
        and all(abs(float(row[i + 2]) - PUBLISHED_RET[row[0]][i]) < 0.01 for i in range(3))
        for row in q2)
    check("sql/13 Q2 matches published retention (Oct–Dec 2017)", ok13r)
    q3 = lines[26].split("|")
    check("sql/13 Q3: min 131.60 / max 167.07 / overall 142.44",
          abs(float(q3[0]) - 131.60) < 0.01 and abs(float(q3[1]) - 167.07) < 0.01
          and abs(float(q3[2]) - 142.44) < 0.01, f"got {q3}")

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
