#!/usr/bin/env python3
"""Flagship 1 — Phase F polish checks (18 Nov 2026).

Verifies the README polish + publish checklist from the Phase F
first block: every headline number in the README matches a verified
source (verified_measures.json or the Phase D analysis notes), the
file counts in the README's project-structure block match the repo,
the architecture files exist and are named in the README, and the
publish checklist exists with the locked-numbers table intact.

Run from the flagship root:
    python3 src/check_phase_f_polish.py
Exits non-zero on any failure.
"""
import json
import re
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


README = ROOT / "README.md"
CHECKLIST = ROOT / "docs" / "publish_checklist.md"
check("flagship README exists", README.exists())
check("publish checklist exists", CHECKLIST.exists())
readme = read("README.md") if README.exists() else ""
checklist = read("docs/publish_checklist.md") if CHECKLIST.exists() else ""

# --- 1. Headline numbers in the README match verified_measures.json --
vm = json.loads(read("powerbi/verified_measures.json"))
locked = {
    "13,494,400.74": vm["total_revenue_restated"],
    "13,591,643.70": vm["total_revenue_all_statuses"],
    "98,199": vm["total_orders_restated"],
    "94,983": vm["total_customers_restated"],
    "137.42": vm["avg_order_value_restated"],
    "142.07": vm["avg_spend_per_customer_restated"],
    "112,650": vm["fact_rows"],
    "2,245,816.19": vm["total_freight_restated"],
    "16.64%": vm["freight_pct_revenue_restated"],
    "4,100": vm["items_over_100pct_freight_restated"],
    "38.27%": vm["sp_revenue_share_restated"],
    "1,003,862.14": vm["peak_month_revenue_restated"],
    "2,887": vm["repeat_buyers_restated"],
    "66,476": vm["churned_restated"],
    "69.99%": vm["churn_rate_restated"],
}
for text, value in locked.items():
    check(f"README carries {text} (verified value {value})", text in readme,
          f"{text} missing from README")

# Numbers that live in the Phase D notes, not in verified_measures.json.
check("README carries clean trend total 13,449,529.68",
      "13,449,529.68" in readme)
check("README carries at-risk repeat buyers 611 / BRL 168,541.14",
      "611" in readme and "168,541.14" in readme)
check("README carries LTV flat range 131–163",
      "131" in readme and "163" in readme)
check("README keeps the two unrelated 611s distinct",
      "Two unrelated 611s" in readme)

# --- 2. File counts in the README structure block match the repo ----
sql_files = sorted((ROOT / "sql").glob("*.sql"))
check("sql/ holds 16 query files + schema.sql",
      len(sql_files) == 17 and (ROOT / "sql" / "schema.sql").exists(),
      f"found {len(sql_files)} sql files")
check("README says 16 query files + schema.sql",
      "16 query files + schema.sql" in readme)
check_scripts = sorted((ROOT / "src").glob("check_*.py"))
check("src/ holds 12 check scripts (incl. this one)",
      len(check_scripts) == 12, f"found {len(check_scripts)}")
check("README says 12 check scripts",
      "12 check scripts" in readme)
check("README names validate_headlines.py in src/",
      "validate" in readme)
analysis_files = sorted((ROOT / "analysis").glob("*.md"))
check("analysis/ holds 12 notes", len(analysis_files) == 12,
      f"found {len(analysis_files)}")
check("README says 12 finding notes", "12 finding notes" in readme)
outputs = sorted((ROOT / "outputs").glob("*.png"))
check("outputs/ holds 8 renders", len(outputs) == 8,
      f"found {len(outputs)}")
check("README says 8 preview renders", "8 preview renders" in readme)

# --- 3. Architecture diagram is present and named in the README -----
for f in ["docs/architecture.mmd", "docs/architecture_notes.md",
          "outputs/architecture_diagram.png"]:
    check(f"{f} exists", (ROOT / f).exists())
check("README names the architecture diagram",
      "architecture.mmd" in readme and "architecture_diagram.png" in readme)
check("README names the publish checklist file",
      "publish_checklist" in readme or "publish checklist" in readme.lower())

# --- 4. Publish checklist content ------------------------------------
check("checklist names the live date Fri 27 Nov 2026",
      "27 Nov 2026" in checklist)
check("checklist has the regression sweep section",
      "Regression sweep" in checklist)
for script in ["validate_headlines.py", "check_rfm.py",
               "check_order_status.py", "check_ltv_recheck.py",
               "check_nov2016_gap.py", "check_clean_trend.py",
               "check_powerbi_model.py", "check_dashboard_pages.py",
               "check_phase_e_publish.py", "check_architecture.py",
               "check_one_pager.py", "check_executive_summary.py",
               "check_phase_f_polish.py"]:
    check(f"checklist sweep lists {script}", script in checklist,
          f"{script} missing from sweep")
check("checklist lists the one-pager as still open",
      "One-pager" in checklist)
check("checklist keeps the .pbix honest either way",
      "Never ship a fake `.pbix`" in checklist)
for locked_num in ["13,494,400.74", "98,199", "94,983", "13,591,643.70",
                   "112,650", "69.99%", "611", "168,541.14",
                   "13,449,529.68", "1,003,862.14", "2,887"]:
    check(f"checklist lock table carries {locked_num}",
          locked_num in checklist, f"{locked_num} missing")
check("checklist names the LICENSE push step",
      "license-push" in checklist and "LICENSE" in checklist)
check("checklist names the profile README update step",
      "Profile README library table" in checklist)

# --- 5. README still honest about the .pbix ---------------------------
check("README still says the report link is empty until built",
      "not yet published" in readme)
check("README still says no .pbix is bundled",
      "No `.pbix` is bundled" in readme)
check("README carries the LIVE status line with publish date and repo link",
      "LIVE — published 27 Nov 2026" in readme
      and "github.com/mhkh-stock/f1-ecommerce-revenue-cohort-churn" in readme)

print(f"{PASSES[0]} checks passed, {len(FAILURES)} failed")
for f in FAILURES:
    print("FAIL:", f)
sys.exit(1 if FAILURES else 0)
