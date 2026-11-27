#!/usr/bin/env python3
"""Flagship 1 — Phase E third block checks (16 Nov 2026).

Verifies the publish guide + flagship README draft against the
verified model: every file the guide names exists, every KPI in the
publish checklist matches verified_measures.json, every measure in
measures.dax is present, and every headline figure in the README
draft matches a verified source (verified_measures.json or the
Phase B/C/D analysis notes it cites).

Run from the flagship root:
    python3 src/check_phase_e_publish.py
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


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


# --- 1. Files the publish guide + README name must exist -----------
GUIDE = ROOT / "powerbi" / "publish-guide.md"
README = ROOT / "README.md"
check("publish guide exists", GUIDE.exists())
check("flagship README draft exists", README.exists())
guide = read("powerbi/publish-guide.md") if GUIDE.exists() else ""
readme = read("README.md") if README.exists() else ""

for f in [
    "powerbi/build-guide.md",
    "powerbi/measures.dax",
    "powerbi/verified_measures.json",
    "powerbi/page-layouts.md",
    "powerbi/f1_powerbi.db",
    "outputs/page1_overview.png",
    "outputs/page2_revenue_leak.png",
    "outputs/page3_cohorts_churn.png",
    "outputs/preview_monthly_revenue.png",
    "analysis/clean_trend_2017_2018.md",
    "analysis/recommendations.md",
    "analysis/executive_summary.md",
    "sql/14_order_status_restatement.sql",
    "sql/16_clean_trend_2017_2018.sql",
    "PLAN.md",
]:
    check(f"referenced file exists: {f}", (ROOT / f).exists())

# Guide must say the .pbix is NOT bundled and the link slot is empty.
check("guide states no .pbix bundled", "No `.pbix` is bundled" in guide
      or "no `.pbix` is bundled" in guide.lower()
      or ".pbix` itself is" in guide)
check("guide states refresh is not needed (frozen dataset)",
      "No scheduled refresh is needed" in guide)
check("guide states Pro licence requirement",
      "Power BI Pro" in guide)
check("README marks the report link as not yet published",
      "not yet published" in readme)
check("README states target live date", "Fri 27 Nov 2026" in readme)
check("README states no .pbix bundled", "No `.pbix` is bundled" in readme)

# --- 2. Verified measures ------------------------------------------
vm = json.loads(read("powerbi/verified_measures.json"))
dax = read("powerbi/measures.dax")

EXPECTED_MEASURES = [
    "Total Revenue (Restated)",
    "Total Revenue (All Statuses)",
    "Total Orders (Restated)",
    "Total Customers (Restated)",
    "Total Freight (Restated)",
    "Freight % of Revenue",
    "Avg Order Value (Restated)",
    "Avg Spend per Customer (Restated)",
    "Repeat Buyer Rate",
    "Churn Rate",
    "Items Over 100% Freight",
    "SP Revenue Share",
    "Peak Month Revenue",
]
for m in EXPECTED_MEASURES:
    check(f"DAX measure present: {m}", f"{m} =" in dax)
check("DAX measure count is 13 definitions (12 + all-status footnote)",
      len(re.findall(r"^.+ =$\n", dax, flags=re.M)) == 13,
      f"found {len(re.findall(r'^.+ =$', dax, flags=re.M))}")

# Every verified value the publish checklist quotes must appear in
# the guide with the exact figure from verified_measures.json.
def money(v):
    return f"{v:,.2f}"

checklist = [
    ("Total Revenue (Restated)", money(vm["total_revenue_restated"])),
    ("Total Orders (Restated)", f"{vm['total_orders_restated']:,}"),
    ("Total Customers (Restated)", f"{vm['total_customers_restated']:,}"),
    ("Avg Order Value", money(vm["avg_order_value_restated"])),
    ("Churn Rate", f"{vm['churn_rate_restated']:.2f}%"),
    ("Peak Month Revenue", money(vm["peak_month_revenue_restated"])),
    ("all-status revenue", money(vm["total_revenue_all_statuses"])),
    ("Total Freight (Restated)", money(vm["total_freight_restated"])),
    ("Freight % of Revenue", f"{vm['freight_pct_revenue_restated']:.2f}%"),
    ("Items Over 100% Freight", f"{vm['items_over_100pct_freight_restated']:,}"),
    ("SP share", f"{vm['sp_revenue_share_restated']:.2f}%"),
    ("Repeat buyers", f"{vm['repeat_buyers_restated']:,}"),
]
for name, val in checklist:
    check(f"publish checklist quotes {name} = {val}", val in guide, "not in guide")

# Same figures must appear in the README draft.
for name, val in checklist:
    check(f"README quotes {name} = {val}", val in readme, "not in README")

# --- 3. README figures that come from the analysis notes ------------
# At-risk repeat buyers 611 / BRL 168,541.14 (sql/14 restatement).
restatement = read("analysis/order_status_restatement.md")
check("restatement note holds 611 / 168,541.14",
      "611" in restatement and "168,541.14" in restatement)
check("README quotes at-risk 611 / BRL 168,541.14",
      "611" in readme and "168,541.14" in readme)
# Electronics over-100% items: 611 of 2,767 (the other 611).
freight = read("analysis/freight_by_category_findings.md")
check("freight note holds electronics 611 of 2,767",
      "611 of its 2,767 items" in freight)
check("README keeps the two 611s distinct",
      "611 `eletronicos` items" in readme and "611 at-risk repeat buyers" in readme)
# Clean trend total.
trend = read("analysis/clean_trend_2017_2018.md")
check("README quotes clean trend total BRL 13,449,529.68",
      "13,449,529.68" in readme and "13,449,529.68" in trend)
# Cohort LTV flat range (restated: 20 cohorts Jan 2017-Aug 2018).
ltv = read("analysis/cohort_lifetime_value.md")
check("README quotes LTV flat range BRL 131–163",
      "131" in readme and "163" in readme)

# --- 4. Model DB still agrees with verified_measures.json -----------
db = ROOT / "powerbi" / "f1_powerbi.db"
if db.exists():
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute("SELECT COUNT(*) FROM fact_order_items").fetchone()[0]
    check("model DB fact rows = 112,650", rows == 112650, f"got {rows}")
    rev = con.execute(
        "SELECT ROUND(SUM(price), 2) FROM fact_order_items f "
        "JOIN dim_order_status s ON f.order_status = s.order_status "
        "WHERE s.is_restated = 1").fetchone()[0]
    check("model DB restated revenue matches verified_measures.json",
          abs(rev - vm["total_revenue_restated"]) < 0.01, f"got {rev}")
    con.close()
else:
    check("model DB exists", False, "missing")

# --- 5. Publish-guide checklist has all 16 rows ----------------------
rows = re.findall(r"^\| \d+ \|", guide, flags=re.M)
check("publish checklist has 16 rows", len(rows) == 16, f"found {len(rows)}")

print(f"{PASSES[0]} checks passed, {len(FAILURES)} failed")
for f in FAILURES:
    print("FAIL:", f)
sys.exit(1 if FAILURES else 0)
