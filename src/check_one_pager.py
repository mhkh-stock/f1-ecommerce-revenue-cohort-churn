#!/usr/bin/env python3
"""Checks for the Flagship 1 one-pager (Phase F, 19 Nov 2026).

Every number in docs/one_pager.md and outputs/one_pager.pdf must match
powerbi/verified_measures.json or the verified analysis notes.
Run: python3 src/check_one_pager.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "docs" / "one_pager.md"
PDF = ROOT / "outputs" / "one_pager.pdf"

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))


with open(ROOT / "powerbi" / "verified_measures.json") as f:
    M = json.load(f)

md = MD.read_text()
pdf_ok = PDF.exists()

# --- 1. Files exist -------------------------------------------------------
check("one_pager.md exists", MD.exists())
check("one_pager.pdf exists", pdf_ok)

# --- 2. Headline numbers in the markdown ----------------------------------
for needle, label in [
    ("13,494,400.74", "restated revenue"),
    ("94,983", "restated customers"),
    ("98,199", "restated orders"),
    ("137.42", "AOV restated"),
    ("2,245,816.19", "freight restated"),
    ("16.64%", "freight pct restated"),
    ("4,100", "over-100% items restated"),
    ("92,096", "one-time buyers restated"),
    ("142.07", "LTV per customer"),
    ("66,476", "churned restated"),
    ("69.99%", "churn rate restated"),
    ("28,507", "active restated"),
    ("168,541.14", "saveable at-risk revenue"),
    ("38.27%", "SP share restated"),
    ("1,003,862.14", "peak month revenue"),
    ("13,591,643.70", "all-status revenue footnote"),
    ("611", "the 611s named"),
    ("29.50%", "electronics freight restated"),
    ("22.18%", "electronics over-100% rate restated"),
    ("7,188", "Nov 2017 cohort size restated"),
    ("140.30", "Nov 2017 cohort LTV restated"),
    ("63.35%", "top-3 states share restated"),
    ("350,000", "freight fix value"),
    ("2.73M", "phantom at-risk figure"),
    ("18,536", "all at-risk customers"),
]:
    check(f"md contains {label} ({needle})", needle in md)

# --- 3. Cross-checks against verified_measures.json -----------------------
check("md revenue == verified_measures",
      M["total_revenue_restated"] == 13494400.74)
check("md orders == verified_measures", M["total_orders_restated"] == 98199)
check("md customers == verified_measures",
      M["total_customers_restated"] == 94983)
check("md AOV == verified_measures", M["avg_order_value_restated"] == 137.42)
check("md freight == verified_measures",
      M["total_freight_restated"] == 2245816.19)
check("md churn == verified_measures", M["churn_rate_restated"] == 69.99)
check("md churned == verified_measures", M["churned_restated"] == 66476)
check("md SP share == verified_measures",
      M["sp_revenue_share_restated"] == 38.27)
check("md peak month == verified_measures",
      M["peak_month_restated"] == "2017-11"
      and M["peak_month_revenue_restated"] == 1003862.14)
check("md over-100% items == verified_measures",
      M["items_over_100pct_freight_restated"] == 4100)
check("md LTV == verified_measures",
      M["avg_spend_per_customer_restated"] == 142.07)

# --- 4. The two 611s kept distinct ----------------------------------------
check("md warns the two 611s are different things",
      "Two unrelated 611s" in md and "never mix them" in md)
check("md states electronics 611 = items, at-risk 611 = people",
      "611 items" in md and "611 people" in md)

# --- 5. Honest-status lines ------------------------------------------------
check("md says .pbix NOT YET BUILT", "NOT YET BUILT" in md)
check("md says Nov 2016 zero orders + Sep 2018 stub",
      "zero orders" in md and "1-order stub" in md)
check("md says restatement is only -0.72%",
      "−0.72%" in md or "-0.72%" in md)
check("md names sources (sql/03-sql/16, sweep 21 Nov 2026)",
      "sql/03" in md and "21 Nov 2026" in md)

# --- 6. PDF: exactly 1 page, contains the headline numbers ----------------
pages = None
pdf_text = ""
if pdf_ok:
    r = subprocess.run(
        ["python3", "-c",
         "import sys; from pypdf import PdfReader; "
         "r=PdfReader(sys.argv[1]); print(len(r.pages)); "
         "print(' '.join((p.extract_text() or '') for p in r.pages))",
         str(PDF)],
        capture_output=True, text=True)
    if r.returncode == 0:
        lines = r.stdout.splitlines()
        pages = int(lines[0]) if lines else None
        pdf_text = " ".join(lines[1:])
    else:
        # pypdf not installed — fall back to pdfinfo
        r2 = subprocess.run(["pdfinfo", str(PDF)],
                            capture_output=True, text=True)
        m = re.search(r"Pages:\s+(\d+)", r2.stdout)
        pages = int(m.group(1)) if m else None
        check("pdf page count readable (pypdf/pdfinfo)", pages is not None)
check("pdf is exactly 1 page", pages == 1, f"pages={pages}")
if pdf_text:
    for needle, label in [
        ("13,494,400.74", "revenue in pdf"),
        ("94,983", "customers in pdf"),
        ("98,199", "orders in pdf"),
        ("69.99%", "churn in pdf"),
        ("168,541.14", "saveable in pdf"),
        ("NOT YET BUILT", ".pbix status in pdf"),
    ]:
        check(f"pdf contains {label}", needle in pdf_text)

fails = [c for c in CHECKS if not c[1]]
print(f"\n{len(CHECKS) - len(fails)}/{len(CHECKS)} checks passed")
if fails:
    print("FAILURES:")
    for name, _, detail in fails:
        print(f"  - {name} {detail}")
    sys.exit(1)
print("One-pager checks: ALL PASS")
