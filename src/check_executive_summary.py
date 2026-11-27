#!/usr/bin/env python3
"""Flagship 1 — Phase F executive-summary final-pass checks (21 Nov 2026).

Verifies the FINAL executive summary (analysis/executive_summary.md)
against the restated numbers: every figure in the summary is
recomputed from the Power BI model DB (powerbi/f1_powerbi.db) or
read from powerbi/verified_measures.json, and the summary text is
checked to carry the restated strings — and NOT the all-status
strings the 13 Nov draft carried (4,119 / 92,507 / 131-167 /
38.28% / 22.08% / 7,217 / 140.63 / 63.36% / 0.55% / 0.70%).

The Phase B/C analysis notes (cohort_lifetime_value.md, rfm_churn.md,
recommendations.md) correctly report the all-status figures with
their own basis and are NOT touched by this script — only the
publish-facing summary must be restated throughout.

Run from the flagship root:
    python3 src/check_executive_summary.py
Exits non-zero on any failure.
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILURES = []
PASSES = [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
    else:
        FAILURES.append(f"{name}: {detail}")


def close(a, b, tol=0.05):
    return abs(a - b) <= tol


SUMMARY = ROOT / "analysis" / "executive_summary.md"
check("executive summary exists", SUMMARY.exists())
md = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""

# --- 1. Status: FINAL, restated basis stated --------------------------
check("summary is marked FINAL (Phase F final pass)",
      "FINAL" in md and "21 Nov 2026" in md)
check("summary states the restated basis",
      "restated" in md.lower() and "unless labelled" in md)

# --- 2. Restated strings the summary must carry -----------------------
for needle, label in [
    ("13,494,400.74", "restated revenue"),
    ("94,983", "restated customers"),
    ("98,199", "restated orders"),
    ("97.0%", "one-time buyer share restated"),
    ("142.07", "avg spend per customer"),
    ("69.99%", "churn rate restated"),
    ("13,591,643.70", "all-status revenue footnote"),
    ("2,245,816.19", "freight restated"),
    ("4,100", "over-100% items restated"),
    ("3.6%", "over-100% share restated"),
    ("92,096", "one-time buyers restated"),
    ("131–163", "LTV range restated"),
    ("66,476", "churned restated"),
    ("28,507", "active restated"),
    ("168,541.14", "saveable at-risk revenue"),
    ("611", "the 611s named"),
    ("38.27%", "SP share restated"),
    ("63.35%", "top-3 states share restated"),
    ("9.31%", "top category share restated"),
    ("1,003,862.14", "peak month revenue"),
    ("7,421", "peak month orders"),
    ("+49.38%", "Aug 2018 YoY"),
    ("29.50%", "electronics freight restated"),
    ("22.18%", "electronics over-100% rate restated"),
    ("7,188", "Nov 2017 cohort size restated"),
    ("140.30", "Nov 2017 cohort LTV restated"),
    ("0.56%", "month-1 retention Nov 2017 restated"),
    ("0.71%", "month-1 retention Oct 2017 restated"),
    ("98.62", "2016 cohort churn restated"),
    ("99.24", "2017 cohort churn restated"),
    ("120,098", "Jan 2017 revenue"),
    ("152.60", "Jan 2017 AOV"),
    ("126–145", "2018 AOV band restated"),
    ("+242%", "Feb 2018 YoY"),
    ("+177.88%", "H1 2018 vs H1 2017"),
    ("18,536", "all at-risk customers restated"),
    ("2.73M", "phantom at-risk figure"),
    ("97,242.96", "restatement gap"),
    ("0.72%", "restatement share"),
    ("13,221,498.11", "delivered-only revenue"),
    ("1,721", "in-flight orders"),
    ("59.50–69.99%", "churn range by cut-off"),
    ("2,755", "electronics items restated"),
    ("350,000", "freight fix value"),
]:
    check(f"summary carries {label} ({needle})", needle in md)

# --- 3. All-status strings the summary must NOT carry ------------------
# (the as-loaded revenue footnote is the one allowed all-status figure)
for needle, label in [
    ("4,119", "over-100% items all-status"),
    ("92,507", "one-time buyers all-status"),
    ("131–167", "LTV range all-status"),
    ("38.28%", "SP share all-status"),
    ("22.08%", "electronics over-100% rate all-status"),
    ("7,217", "Nov 2017 cohort size all-status"),
    ("140.63", "Nov 2017 cohort LTV all-status"),
    ("63.36%", "top-3 states share all-status"),
    ("9.26%", "top category share all-status"),
    ("0.55%", "month-1 retention Nov 2017 all-status"),
    ("0.70%", "month-1 retention Oct 2017 all-status"),
    ("96.9%", "one-time share all-status"),
    ("18,594", "at-risk customers all-status"),
    ("126–147", "2018 AOV band (never verified)"),
    ("98.71", "2016 cohort churn all-status"),
    ("99.23", "2017 cohort churn all-status"),
    ("2,767", "electronics items all-status"),
    ("1,014,927.64", "Nov 2017 cohort revenue all-status"),
]:
    check(f"summary has no all-status {label} ({needle})",
          needle not in md, f"found {needle}")

# --- 4. Cross-checks against verified_measures.json --------------------
vm = json.loads((ROOT / "powerbi" / "verified_measures.json").read_text())
check("vm restated revenue", vm["total_revenue_restated"] == 13494400.74)
check("vm restated orders", vm["total_orders_restated"] == 98199)
check("vm restated customers", vm["total_customers_restated"] == 94983)
check("vm freight restated", vm["total_freight_restated"] == 2245816.19)
check("vm freight pct", close(vm["freight_pct_revenue_restated"], 16.64))
check("vm over-100% items restated",
      vm["items_over_100pct_freight_restated"] == 4100)
check("vm SP share restated", close(vm["sp_revenue_share_restated"], 38.27))
check("vm peak month revenue",
      vm["peak_month_revenue_restated"] == 1003862.14)
check("vm repeat buyers restated", vm["repeat_buyers_restated"] == 2887)
check("vm churned restated", vm["churned_restated"] == 66476)
check("vm avg spend", vm["avg_spend_per_customer_restated"] == 142.07)

# --- 5. Recompute from the model DB ------------------------------------
R = "f.order_status NOT IN ('canceled','unavailable')"
db = ROOT / "powerbi" / "f1_powerbi.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

# One-time buyers = restated customers - restated repeat buyers.
one_time = con.execute(
    f"SELECT COUNT(*) FROM (SELECT cu.customer_unique_id "
    f"FROM fact_order_items f JOIN dim_customer cu "
    f"ON cu.customer_id = f.customer_id WHERE {R} "
    f"GROUP BY cu.customer_unique_id "
    f"HAVING COUNT(DISTINCT f.order_id) = 1)").fetchone()[0]
check("one-time buyers restated = 92,096", one_time == 92096,
      f"got {one_time:,}")

# At-risk (sql/14 Q7 windows) + at-risk repeat buyers.
atrisk = con.execute(
    f"WITH in_window AS (SELECT DISTINCT cu.customer_unique_id "
    f"FROM dim_customer cu JOIN fact_order_items f "
    f"ON f.customer_id = cu.customer_id JOIN dim_date d "
    f"ON d.date_id = f.date_id WHERE {R} "
    f"AND d.date_id >= '2018-04-17' AND d.date_id < '2018-07-17'), "
    f"after_window AS (SELECT DISTINCT cu.customer_unique_id "
    f"FROM dim_customer cu JOIN fact_order_items f "
    f"ON f.customer_id = cu.customer_id JOIN dim_date d "
    f"ON d.date_id = f.date_id WHERE {R} "
    f"AND d.date_id >= '2018-07-17'), "
    f"at_risk AS (SELECT customer_unique_id FROM in_window EXCEPT "
    f"SELECT customer_unique_id FROM after_window) "
    f"SELECT (SELECT COUNT(*) FROM at_risk), "
    f"ROUND((SELECT SUM(f.price) FROM fact_order_items f "
    f"JOIN dim_customer cu ON cu.customer_id = f.customer_id "
    f"WHERE {R} AND cu.customer_unique_id IN "
    f"(SELECT customer_unique_id FROM at_risk)), 2)").fetchone()
check("at-risk customers restated = 18,536", atrisk[0] == 18536,
      f"got {atrisk[0]:,}")
check("at-risk revenue restated = BRL 2,733,862.67",
      close(atrisk[1], 2733862.67, 0.01), f"got {atrisk[1]:,.2f}")
ar_rep = con.execute(
    f"WITH in_window AS (SELECT DISTINCT cu.customer_unique_id "
    f"FROM dim_customer cu JOIN fact_order_items f "
    f"ON f.customer_id = cu.customer_id JOIN dim_date d "
    f"ON d.date_id = f.date_id WHERE {R} "
    f"AND d.date_id >= '2018-04-17' AND d.date_id < '2018-07-17'), "
    f"after_window AS (SELECT DISTINCT cu.customer_unique_id "
    f"FROM dim_customer cu JOIN fact_order_items f "
    f"ON f.customer_id = cu.customer_id JOIN dim_date d "
    f"ON d.date_id = f.date_id WHERE {R} "
    f"AND d.date_id >= '2018-07-17'), "
    f"at_risk AS (SELECT customer_unique_id FROM in_window EXCEPT "
    f"SELECT customer_unique_id FROM after_window), "
    f"at_risk_repeat AS (SELECT cu.customer_unique_id "
    f"FROM fact_order_items f JOIN dim_customer cu "
    f"ON cu.customer_id = f.customer_id WHERE {R} "
    f"AND cu.customer_unique_id IN (SELECT customer_unique_id "
    f"FROM at_risk) GROUP BY cu.customer_unique_id "
    f"HAVING COUNT(DISTINCT f.order_id) > 1) "
    f"SELECT COUNT(*), ROUND(SUM(rev), 2) FROM (SELECT "
    f"cu.customer_unique_id, SUM(f.price) rev FROM fact_order_items f "
    f"JOIN dim_customer cu ON cu.customer_id = f.customer_id "
    f"WHERE {R} AND cu.customer_unique_id IN "
    f"(SELECT customer_unique_id FROM at_risk_repeat) "
    f"GROUP BY cu.customer_unique_id)").fetchone()
check("at-risk repeat buyers restated = 611", ar_rep[0] == 611,
      f"got {ar_rep[0]:,}")
check("at-risk repeat revenue = BRL 168,541.14",
      close(ar_rep[1], 168541.14, 0.01), f"got {ar_rep[1]:,.2f}")

# Electronics over-100% items restated (the other 611).
elec = con.execute(
    f"SELECT COUNT(*), (SELECT COUNT(*) FROM fact_order_items f "
    f"JOIN dim_product p ON p.product_id = f.product_id "
    f"WHERE {R} AND p.product_category_name = 'eletronicos') "
    f"FROM fact_order_items f JOIN dim_product p "
    f"ON p.product_id = f.product_id WHERE {R} "
    f"AND p.product_category_name = 'eletronicos' "
    f"AND f.freight_value > f.price").fetchone()
check("electronics over-100% items restated = 611", elec[0] == 611,
      f"got {elec[0]:,}")
check("electronics items restated = 2,755", elec[1] == 2755,
      f"got {elec[1]:,}")
check("electronics over-100% rate restated = 22.18%",
      close(100.0 * elec[0] / elec[1], 22.18), 
      f"got {100.0 * elec[0] / elec[1]:.2f}%")
elec_freight = con.execute(
    f"SELECT ROUND(100.0 * SUM(f.freight_value) / SUM(f.price), 2) "
    f"FROM fact_order_items f JOIN dim_product p "
    f"ON p.product_id = f.product_id WHERE {R} "
    f"AND p.product_category_name = 'eletronicos'").fetchone()[0]
check("electronics freight restated = 29.50%",
      close(elec_freight, 29.50), f"got {elec_freight}%")

# Cohort LTV restated (20 cohorts Jan 2017-Aug 2018) + Nov 2017 cohort.
ltv = con.execute(
    f"SELECT cohort, SUM(revenue) / COUNT(DISTINCT customer_unique_id) "
    f"FROM (SELECT cu.customer_unique_id, "
    f"substr(MIN(f.date_id), 1, 7) cohort, SUM(f.price) revenue "
    f"FROM fact_order_items f JOIN dim_customer cu "
    f"ON cu.customer_id = f.customer_id WHERE {R} "
    f"GROUP BY cu.customer_unique_id) "
    f"WHERE cohort >= '2017-01' AND cohort <= '2018-08' "
    f"GROUP BY cohort ORDER BY cohort").fetchall()
check("LTV = 20 cohorts Jan 2017-Aug 2018", len(ltv) == 20,
      f"{len(ltv)} cohorts")
check("LTV range restated BRL 131.21-163.49",
      close(min(v for _, v in ltv), 131.21) and
      close(max(v for _, v in ltv), 163.49),
      f"BRL {min(v for _, v in ltv):.2f}-{max(v for _, v in ltv):.2f}")
nov = con.execute(
    f"WITH firsts AS (SELECT cu.customer_unique_id, "
    f"MIN(d.date_id) AS first_date FROM fact_order_items f "
    f"JOIN dim_customer cu ON cu.customer_id = f.customer_id "
    f"JOIN dim_date d ON d.date_id = f.date_id WHERE {R} "
    f"GROUP BY cu.customer_unique_id) "
    f"SELECT COUNT(*), ROUND(SUM(s.spent), 2), ROUND(AVG(s.spent), 2) "
    f"FROM firsts JOIN (SELECT cu.customer_unique_id, "
    f"SUM(f.price) AS spent FROM fact_order_items f "
    f"JOIN dim_customer cu ON cu.customer_id = f.customer_id "
    f"WHERE {R} GROUP BY cu.customer_unique_id) s "
    f"USING (customer_unique_id) "
    f"WHERE substr(first_date, 1, 7) = '2017-11'").fetchone()
check("Nov 2017 cohort restated = 7,188 customers", nov[0] == 7188,
      f"got {nov[0]:,}")
check("Nov 2017 cohort revenue restated = BRL 1,008,457.51",
      close(nov[1], 1008457.51, 0.01), f"got {nov[1]:,.2f}")
check("Nov 2017 cohort LTV restated = BRL 140.30",
      close(nov[2], 140.30), f"got {nov[2]:.2f}")

# Month-1 retention restated (same logic as check_dashboard_pages.py).
def retention(cohort, k):
    n_cohort, n_active = con.execute(
        f"WITH first_buy AS (SELECT cu.customer_unique_id, "
        f"substr(MIN(f.date_id), 1, 7) cohort FROM fact_order_items f "
        f"JOIN dim_customer cu ON cu.customer_id = f.customer_id "
        f"WHERE {R} GROUP BY cu.customer_unique_id) "
        f"SELECT (SELECT COUNT(*) FROM first_buy WHERE cohort = ?), "
        f"COUNT(DISTINCT cu.customer_unique_id) FROM fact_order_items a "
        f"JOIN dim_customer cu ON cu.customer_id = a.customer_id "
        f"JOIN first_buy fb "
        f"ON fb.customer_unique_id = cu.customer_unique_id "
        f"WHERE a.order_status NOT IN ('canceled','unavailable') "
        f"AND fb.cohort = ? AND substr(a.date_id, 1, 7) = ?",
        (cohort, cohort,
         f"{int(cohort[:4]) + (int(cohort[5:7]) + k - 1) // 12:04d}-"
         f"{(int(cohort[5:7]) + k - 1) % 12 + 1:02d}")).fetchone()
    return 100.0 * n_active / n_cohort

check("month-1 retention Nov 2017 restated = 0.56%",
      close(retention("2017-11", 1), 0.56, 0.02),
      f"{retention('2017-11', 1):.2f}%")
check("month-1 retention Oct 2017 restated = 0.71%",
      close(retention("2017-10", 1), 0.71, 0.02),
      f"{retention('2017-10', 1):.2f}%")

# Yearly cohort churn restated (sql/11 rule: last purchase < 2018-04-17).
ychurn = con.execute(
    f"WITH cust AS (SELECT cu.customer_unique_id, "
    f"MIN(d.date_id) AS first_date, MAX(d.date_id) AS last_date "
    f"FROM fact_order_items f JOIN dim_customer cu "
    f"ON cu.customer_id = f.customer_id JOIN dim_date d "
    f"ON d.date_id = f.date_id WHERE {R} "
    f"GROUP BY cu.customer_unique_id) "
    f"SELECT substr(first_date, 1, 4), "
    f"ROUND(100.0 * SUM(CASE WHEN last_date < '2018-04-17' THEN 1 "
    f"ELSE 0 END) / COUNT(*), 2) FROM cust "
    f"GROUP BY 1 ORDER BY 1").fetchall()
ychurn = dict(ychurn)
check("2016 cohort churn restated = 98.62%",
      close(ychurn["2016"], 98.62), f"got {ychurn['2016']}%")
check("2017 cohort churn restated = 99.24%",
      close(ychurn["2017"], 99.24), f"got {ychurn['2017']}%")

# Geography restated: SP share, top-3 states, top category share.
states = con.execute(
    f"SELECT cu.customer_state, ROUND(SUM(f.price), 2) "
    f"FROM fact_order_items f JOIN dim_customer cu "
    f"ON cu.customer_id = f.customer_id WHERE {R} "
    f"GROUP BY 1 ORDER BY 2 DESC LIMIT 3").fetchall()
rev = vm["total_revenue_restated"]
check("SP share restated = 38.27%",
      close(100.0 * states[0][1] / rev, 38.27),
      f"got {100.0 * states[0][1] / rev:.2f}%")
check("top-3 states share restated = 63.35%",
      close(100.0 * sum(s[1] for s in states) / rev, 63.35),
      f"got {100.0 * sum(s[1] for s in states) / rev:.2f}%")
topcat = con.execute(
    f"SELECT ROUND(SUM(f.price), 2) FROM fact_order_items f "
    f"JOIN dim_product p ON p.product_id = f.product_id "
    f"WHERE {R} GROUP BY p.product_category_name "
    f"ORDER BY 1 DESC LIMIT 1").fetchone()[0]
check("top category share restated = 9.31%",
      close(100.0 * topcat / rev, 9.31),
      f"got {100.0 * topcat / rev:.2f}%")

# Clean trend restated (sql/16 series) — Jan 2017, Nov 2017, 2018 band.
months = con.execute(
    f"SELECT substr(d.date_id, 1, 7), COUNT(DISTINCT f.order_id), "
    f"ROUND(SUM(f.price), 2), "
    f"ROUND(SUM(f.price) / COUNT(DISTINCT f.order_id), 2) "
    f"FROM fact_order_items f JOIN dim_date d "
    f"ON d.date_id = f.date_id WHERE {R} "
    f"AND substr(d.date_id, 1, 7) BETWEEN '2017-01' AND '2018-08' "
    f"GROUP BY 1 ORDER BY 1").fetchall()
m = {row[0]: row for row in months}
check("Jan 2017 restated = 787 orders", m["2017-01"][1] == 787,
      f"got {m['2017-01'][1]:,}")
check("Jan 2017 revenue restated = BRL 120,098.27",
      close(m["2017-01"][2], 120098.27, 0.01),
      f"got {m['2017-01'][2]:,.2f}")
check("Jan 2017 AOV restated = BRL 152.60",
      close(m["2017-01"][3], 152.60), f"got {m['2017-01'][3]:.2f}")
check("Nov 2017 restated = 7,421 orders", m["2017-11"][1] == 7421,
      f"got {m['2017-11'][1]:,}")
check("Nov 2017 revenue restated = BRL 1,003,862.14",
      close(m["2017-11"][2], 1003862.14, 0.01),
      f"got {m['2017-11'][2]:,.2f}")
m18 = [r for k, r in m.items() if k.startswith("2018-")]
check("2018 monthly revenue band BRL 838k-994k",
      close(min(r[2] for r in m18), 837895.43, 0.01) and
      close(max(r[2] for r in m18), 993592.98, 0.01),
      f"BRL {min(r[2] for r in m18):,.0f}-"
      f"{max(r[2] for r in m18):,.0f}")
check("2018 AOV band restated BRL 126-145",
      close(min(r[3] for r in m18), 126.49) and
      close(max(r[3] for r in m18), 145.31),
      f"BRL {min(r[3] for r in m18):.2f}-"
      f"{max(r[3] for r in m18):.2f}")
check("2018 monthly orders 6,145-7,187",
      min(r[1] for r in m18) == 6145 and max(r[1] for r in m18) == 7187,
      f"{min(r[1] for r in m18):,}-{max(r[1] for r in m18):,}")
yoy_feb = 100.0 * (m["2018-02"][2] / m["2017-02"][2] - 1)
yoy_aug = 100.0 * (m["2018-08"][2] / m["2017-08"][2] - 1)
check("Feb 2018 YoY restated = +242.05%", close(yoy_feb, 242.05),
      f"got +{yoy_feb:.2f}%")
check("Aug 2018 YoY restated = +49.38%", close(yoy_aug, 49.38),
      f"got +{yoy_aug:.2f}%")
h1_18 = sum(r[2] for k, r in m.items() if k in
            ("2018-01", "2018-02", "2018-03", "2018-04", "2018-05",
             "2018-06"))
h1_17 = sum(r[2] for k, r in m.items() if k in
            ("2017-01", "2017-02", "2017-03", "2017-04", "2017-05",
             "2017-06"))
check("H1 2018 vs H1 2017 restated = +177.88%",
      close(100.0 * (h1_18 / h1_17 - 1), 177.88),
      f"got +{100.0 * (h1_18 / h1_17 - 1):.2f}%")

# Freight-fix value: 16.64% -> ~14% of restated revenue.
saving = (vm["freight_pct_revenue_restated"] - 14.0) / 100.0 * rev
check("freight fix worth roughly BRL 350,000 (restated basis)",
      330000 <= saving <= 380000, f"computed BRL {saving:,.0f}")

# The two unrelated 611s are both 611 under the restated basis too.
check("two unrelated 611s both hold restated",
      elec[0] == 611 and ar_rep[0] == 611)

con.close()

print(f"{PASSES[0]} checks passed, {len(FAILURES)} failed")
for f in FAILURES:
    print("FAIL:", f)
sys.exit(1 if FAILURES else 0)
