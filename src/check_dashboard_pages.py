#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase E block 2 (15 Nov 2026): checks for the three
dashboard page previews. Every KPI and chart total on pages 1–3 is
recomputed from powerbi/f1_powerbi.db and compared with
powerbi/verified_measures.json, the restatement note
(analysis/order_status_restatement.md) and powerbi/page-layouts.md.

    python3 src/check_dashboard_pages.py
"""
import json
import sqlite3
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "powerbi" / "f1_powerbi.db"
VM = json.loads((PROJECT / "powerbi" / "verified_measures.json").read_text())
R = "order_status NOT IN ('canceled', 'unavailable')"
CHECKS = [0, 0]  # passed, failed


def check(name, cond, detail=""):
    CHECKS[0 if cond else 1] += 1
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    return cond


def close(a, b, tol=0.01):
    return abs(a - b) <= tol


con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

# ---- Page 1 KPIs: recompute from the model DB -------------------------
rev, orders, cust = con.execute(
    f"SELECT SUM(price), COUNT(DISTINCT order_id), "
    f"COUNT(DISTINCT cu.customer_unique_id) FROM fact_order_items f "
    f"JOIN dim_customer cu ON cu.customer_id = f.customer_id WHERE {R}").fetchone()
check("p1 revenue = verified", close(rev, VM["total_revenue_restated"]), f"BRL {rev:,.2f}")
check("p1 orders = verified", orders == VM["total_orders_restated"], f"{orders:,}")
check("p1 customers = verified", cust == VM["total_customers_restated"], f"{cust:,}")
check("p1 AOV = verified", close(rev / orders, VM["avg_order_value_restated"]), f"BRL {rev / orders:.2f}")
churned = con.execute(
    f"SELECT COUNT(*) FROM (SELECT cu.customer_unique_id, MAX(f.date_id) lastd "
    f"FROM fact_order_items f JOIN dim_customer cu ON cu.customer_id = f.customer_id "
    f"WHERE {R} GROUP BY cu.customer_unique_id) WHERE lastd < date('2018-10-17', '-6 months')").fetchone()[0]
check("p1 churn = verified", close(100.0 * churned / cust, VM["churn_rate_restated"], 0.01),
      f"{100.0 * churned / cust:.2f}% ({churned:,} churned)")

# ---- Page 1 charts ------------------------------------------------------
trend = con.execute(
    f"SELECT substr(date_id, 1, 7), SUM(price) FROM fact_order_items "
    f"WHERE {R} AND date_id >= '2017-01-01' AND date_id < '2018-09-01' "
    f"GROUP BY 1 ORDER BY 1").fetchall()
check("p1 trend = 20 months", len(trend) == 20, f"{len(trend)} months")
check("p1 trend total = sql/16 clean total",
      close(sum(v for _, v in trend), 13449529.68), f"BRL {sum(v for _, v in trend):,.2f}")
peak = max(trend, key=lambda r: r[1])
check("p1 trend peak Nov 2017", peak[0] == "2017-11" and close(peak[1], 1003862.14),
      f"{peak[0]} BRL {peak[1]:,.2f}")
cats = con.execute(
    f"SELECT p.product_category_name, SUM(f.price) FROM fact_order_items f "
    f"JOIN dim_product p ON f.product_id = p.product_id WHERE {R} "
    f"GROUP BY 1 ORDER BY 2 DESC LIMIT 10").fetchall()
check("p1 top category beleza_saude", cats[0][0] == "beleza_saude" and close(cats[0][1], 1255695.13),
      f"BRL {cats[0][1]:,.2f}")
check("p1 top-10 categories sum < total revenue",
      sum(v for _, v in cats) < rev, f"BRL {sum(v for _, v in cats):,.2f} of {rev:,.2f}")

# ---- Page 2 KPIs + charts ----------------------------------------------
freight = con.execute(f"SELECT SUM(freight_value) FROM fact_order_items WHERE {R}").fetchone()[0]
check("p2 freight = verified", close(freight, VM["total_freight_restated"]), f"BRL {freight:,.2f}")
check("p2 freight% = verified",
      close(100.0 * freight / rev, VM["freight_pct_revenue_restated"], 0.01),
      f"{100.0 * freight / rev:.2f}%")
over = con.execute(f"SELECT COUNT(*) FROM fact_order_items WHERE {R} AND freight_value > price").fetchone()[0]
check("p2 over-100% items = verified", over == VM["items_over_100pct_freight_restated"], f"{over:,}")
fpct = con.execute(
    f"SELECT p.product_category_name, 100.0 * SUM(f.freight_value) / SUM(f.price) "
    f"FROM fact_order_items f JOIN dim_product p ON f.product_id = p.product_id "
    f"WHERE {R} GROUP BY 1 HAVING COUNT(*) >= 500 ORDER BY 2 DESC LIMIT 10").fetchall()
check("p2 top freight% category eletronicos", fpct[0][0] == "eletronicos" and close(fpct[0][1], 29.50, 0.05),
      f"{fpct[0][1]:.2f}%")
sp = con.execute(
    f"SELECT SUM(f.price) FROM fact_order_items f JOIN dim_customer c "
    f"ON f.customer_id = c.customer_id WHERE {R} AND c.customer_state = 'SP'").fetchone()[0]
check("p2 SP share = verified", close(100.0 * sp / rev, VM["sp_revenue_share_restated"], 0.05),
      f"{100.0 * sp / rev:.2f}%")
sample = con.execute(f"SELECT COUNT(*) FROM fact_order_items WHERE {R} AND (rowid % 23) = 0").fetchone()[0]
check("p2 scatter sample ≈ 1-in-23", 4800 <= sample <= 4950, f"{sample:,} points")

# ---- Page 3 KPIs + charts ----------------------------------------------
repeat = con.execute(
    f"SELECT COUNT(*) FROM (SELECT cu.customer_unique_id FROM fact_order_items f "
    f"JOIN dim_customer cu ON cu.customer_id = f.customer_id WHERE {R} "
    f"GROUP BY cu.customer_unique_id HAVING COUNT(DISTINCT f.order_id) >= 2)").fetchone()[0]
check("p3 repeat buyer rate = verified",
      close(100.0 * repeat / cust, VM["repeat_buyer_rate_restated"], 0.01),
      f"{100.0 * repeat / cust:.2f}% ({repeat:,})")
atrisk = con.execute(
    f"SELECT COUNT(*), SUM(revenue) FROM ("
    f"SELECT cu.customer_unique_id, MAX(f.date_id) lastd, "
    f"COUNT(DISTINCT f.order_id) orders, SUM(f.price) revenue "
    f"FROM fact_order_items f JOIN dim_customer cu ON cu.customer_id = f.customer_id "
    f"WHERE {R} GROUP BY cu.customer_unique_id "
    f"HAVING orders >= 2 AND lastd >= '2018-04-17' AND lastd < '2018-07-17')").fetchone()
check("p3 at-risk repeat buyers = 611", atrisk[0] == 611, f"{atrisk[0]:,}")
check("p3 at-risk revenue = BRL 168,541.14", close(atrisk[1], 168541.14),
      f"BRL {atrisk[1]:,.2f}")


def retention(cohort, k):
    n_cohort, n_active = con.execute(
        f"WITH first_buy AS (SELECT cu.customer_unique_id, "
        f"substr(MIN(f.date_id), 1, 7) cohort FROM fact_order_items f "
        f"JOIN dim_customer cu ON cu.customer_id = f.customer_id WHERE {R} "
        f"GROUP BY cu.customer_unique_id) "
        f"SELECT (SELECT COUNT(*) FROM first_buy WHERE cohort = ?), "
        f"COUNT(DISTINCT cu.customer_unique_id) FROM fact_order_items a "
        f"JOIN dim_customer cu ON cu.customer_id = a.customer_id "
        f"JOIN first_buy fb ON fb.customer_unique_id = cu.customer_unique_id "
        f"WHERE {R} AND fb.cohort = ? AND substr(a.date_id, 1, 7) = ?",
        (cohort, cohort,
         f"{int(cohort[:4]) + (int(cohort[5:7]) + k - 1) // 12:04d}-{(int(cohort[5:7]) + k - 1) % 12 + 1:02d}")).fetchone()
    return 100.0 * n_active / n_cohort


nov1 = retention("2017-11", 1)
oct1 = retention("2017-10", 1)
check("p3 month-1 retention Nov 2017 = 0.56%", close(nov1, 0.56, 0.02), f"{nov1:.2f}%")
check("p3 month-1 retention Oct 2017 = 0.71%", close(oct1, 0.71, 0.02), f"{oct1:.2f}%")
ltv = con.execute(
    f"SELECT cohort, SUM(revenue) / COUNT(DISTINCT customer_unique_id) FROM ("
    f"SELECT cu.customer_unique_id, substr(MIN(f.date_id), 1, 7) cohort, SUM(f.price) revenue "
    f"FROM fact_order_items f JOIN dim_customer cu ON cu.customer_id = f.customer_id "
    f"WHERE {R} GROUP BY cu.customer_unique_id) "
    f"WHERE cohort >= '2017-01' AND cohort <= '2018-08' GROUP BY cohort ORDER BY cohort").fetchall()
check("p3 LTV = 20 cohorts Jan 2017–Aug 2018", len(ltv) == 20, f"{len(ltv)} cohorts")
check("p3 LTV range BRL 131.21–163.49",
      close(min(v for _, v in ltv), 131.21, 0.05) and close(max(v for _, v in ltv), 163.49, 0.05),
      f"BRL {min(v for _, v in ltv):.2f}–{max(v for _, v in ltv):.2f}")

# ---- Files + docs ---------------------------------------------------------
for name in ("page1_overview.png", "page2_revenue_leak.png", "page3_cohorts_churn.png"):
    p = PROJECT / "outputs" / name
    check(f"preview exists: {name}", p.exists() and p.stat().st_size > 100_000,
          f"{p.stat().st_size:,} bytes" if p.exists() else "missing")
layouts = (PROJECT / "powerbi" / "page-layouts.md").read_text()
check("layouts name eletronicos as top freight category",
      "eletronicos 29.50%" in layouts)
check("layouts carry restated retention 0.56% / 0.71%",
      "0.56% (Nov 2017) vs 0.71% (Oct 2017)" in layouts)
guide = (PROJECT / "powerbi" / "build-guide.md").read_text()
check("build guide corrected (no informatica_acessorios as first)",
      "informatica_acessorios`) first" not in guide and "eletronicos" in guide)

con.close()
print(f"\n{CHECKS[0]} checks passed, {CHECKS[1]} failed")
sys.exit(1 if CHECKS[1] else 0)
