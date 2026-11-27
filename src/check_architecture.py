"""FLAGSHIP 1 — check the architecture diagram's factual claims (Phase F prep, 17 Nov 2026).

Asserts that every file the diagram names exists in the project folder,
every number it cites matches verified_measures.json, the live SQLite
databases, or the verified analysis notes — and that the .pbix the diagram
marks "not yet built" genuinely does not exist yet.

Run from the project folder:
    python3 src/check_architecture.py
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MMD = BASE / "docs" / "architecture.mmd"
PNG = BASE / "outputs" / "architecture_diagram.png"

passed = 0
failed = 0
failures = []


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok  {name}")
    else:
        failed += 1
        failures.append(name)
        print(f" FAIL {name}  {detail}")


def read(rel):
    return (BASE / rel).read_text(encoding="utf-8")


# --- 0. Diagram source + render exist --------------------------------------
print("== diagram files ==")
check("docs/architecture.mmd exists", MMD.exists())
check("outputs/architecture_diagram.png exists", PNG.exists())
check("PNG is a real render (> 50 KB)", PNG.exists() and PNG.stat().st_size > 50_000,
      f"size={PNG.stat().st_size if PNG.exists() else 'missing'}")
if PNG.exists():
    head = PNG.read_bytes()[:8]
    check("PNG has a valid PNG header", head == b"\x89PNG\r\n\x1a\n")
mmd = read("docs/architecture.mmd")

# --- 1. Every file the diagram names exists --------------------------------
print("== files named in the diagram ==")
named_files = [
    "data/raw/olist_customers_dataset.csv",
    "data/raw/olist_orders_dataset.csv",
    "data/raw/olist_order_items_dataset.csv",
    "data/raw/olist_products_dataset.csv",
    "data/raw/olist_sellers_dataset.csv",
    "src/download_olist.py",
    "src/ingest.py",
    "src/validate_headlines.py",
    "data/processed/f1.db",
    "sql/schema.sql",
    "sql/12_validation_reconciliation.sql",
    "sql/14_order_status_restatement.sql",
    "powerbi/build_model.py",
    "powerbi/f1_powerbi.db",
    "powerbi/measures.dax",
    "powerbi/verified_measures.json",
    "powerbi/publish-guide.md",
    "outputs/page1_overview.png",
    "outputs/page2_revenue_leak.png",
    "outputs/page3_cohorts_churn.png",
]
for f in named_files:
    check(f"file exists: {f}", (BASE / f).exists())

# --- 2. Counts the diagram cites -------------------------------------------
print("== counts ==")
raw_csvs = sorted((BASE / "data" / "raw").glob("olist_*.csv"))
check("5 raw Olist CSVs in data/raw/", len(raw_csvs) == 5, f"got {len(raw_csvs)}")
numbered_sql = sorted((BASE / "sql").glob("[0-9][0-9]_*.sql"))
check("16 numbered SQL queries (sql/01–16)", len(numbered_sql) == 16,
      f"got {len(numbered_sql)}")
dax = read("powerbi/measures.dax")
dax_defs = re.findall(r"(?m)^[A-Za-z][A-Za-z0-9 ()%]+ =$", dax)
check("13 DAX definitions = 12 measures + 1 all-status footnote",
      len(dax_defs) == 13, f"got {len(dax_defs)}: {dax_defs}")
check("diagram says '12 DAX measures + 1 footnote measure'",
      "12 DAX measures + 1 footnote measure" in mmd)
check("'11 headlines reconciled' is the verified verdict",
      "ALL 11 HEADLINES RECONCILE" in read("analysis/validation_notes.md"))
check("diagram says '11 headlines reconciled 3 ways'",
      "11 headlines reconciled" in mmd and "3 ways" in mmd)

# --- 3. Numbers vs verified_measures.json -----------------------------------
print("== numbers vs verified_measures.json ==")
vm = json.loads(read("powerbi/verified_measures.json"))
expected = {
    "fact_rows": ("112,650", "fact rows"),
    "total_revenue_restated": ("13,494,400.74", "restated revenue BRL"),
    "total_orders_restated": ("98,199", "restated orders"),
    "total_customers_restated": ("94,983", "restated customers"),
    "churn_rate_restated": ("69.99%", "churn rate"),
    "freight_pct_revenue_restated": ("16.64%", "freight % of revenue"),
    "avg_order_value_restated": ("137.42", "avg order value BRL"),
}
for key, (text, label) in expected.items():
    val = vm[key]
    if isinstance(val, float):
        ok = abs(val - float(text.replace(",", "").rstrip("%"))) < 0.005
    else:
        ok = str(val) == text.replace(",", "")
    check(f"verified_measures.json {label} = {text}", ok, f"got {val}")
    check(f"diagram cites {label} ({text})", text in mmd)

# --- 4. Numbers vs the live databases ---------------------------------------
print("== numbers vs live databases ==")
con = sqlite3.connect(BASE / "data" / "processed" / "f1.db")
db_counts = {
    "fact_order_items": 112650,
    "dim_customer": 99441,
    "dim_product": 32951,
    "dim_seller": 3095,
    "dim_date": 634,
}
for table, want in db_counts.items():
    got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    check(f"f1.db {table} = {want:,}", got == want, f"got {got:,}")
    check(f"diagram cites {table} {want:,}", f"{want:,}" in mmd)
con.close()

model = sqlite3.connect(BASE / "powerbi" / "f1_powerbi.db")
got = model.execute("SELECT COUNT(*) FROM fact_order_items").fetchone()[0]
check("model DB fact rows = 112,650", got == 112650, f"got {got:,}")
check("model DB has dim_order_status", model.execute(
    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='dim_order_status'"
).fetchone()[0] == 1)
model.close()

# --- 5. Ingest claim ---------------------------------------------------------
print("== ingest claim ==")
check("'0 rejected' is the recorded ingest result",
      "0 rejected" in read("data/README.md"))
check("diagram says '112,650 rows kept · 0 rejected'",
      "112,650 rows kept" in mmd and "0 rejected" in mmd)
check("dataset window 'Sep 2016 – Aug 2018' matches the executive summary",
      "Sep 2016" in read("analysis/executive_summary.md")
      and "Aug 2018" in read("analysis/executive_summary.md"))

# --- 6. The pending .pbix is genuinely pending -------------------------------
print("== pending .pbix ==")
pbix = list(BASE.rglob("*.pbix"))
check("no .pbix exists anywhere in the project (diagram: NOT YET BUILT)",
      pbix == [], f"found {pbix}")
check("diagram marks the .pbix NOT YET BUILT", "NOT YET BUILT" in mmd)
check("diagram leaves the published link empty", "empty until the .pbix exists" in mmd)

# --- summary -----------------------------------------------------------------
print(f"\n{passed} checks passed, {failed} failed.")
if failed:
    print("Failures:", *failures, sep="\n  - ")
    sys.exit(1)
