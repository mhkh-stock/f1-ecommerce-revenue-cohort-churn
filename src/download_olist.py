"""Download the 5 Olist CSVs the F1 ingest loader needs, from the public
GitHub mirror that hosts the Kaggle Brazilian E-Commerce dataset files
(olist/work-at-olist-data, datasets/, official Olist repo). Verifies each
file by checking its header row against the known Olist schema before
accepting it. Writes to data/raw/ (NOT shipped as repo data — the repo
ships the loader + the SQLite star, raw CSVs stay local build input).
"""
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
FILES = {
    "olist_customers_dataset.csv": "customer_id",
    "olist_products_dataset.csv": "product_id",
    "olist_sellers_dataset.csv": "seller_id",
    "olist_orders_dataset.csv": "order_id",
    "olist_order_items_dataset.csv": "order_id",
}
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

ok = True
for name, first_col in FILES.items():
    dest = OUT / name
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"skip (exists): {name}")
        continue
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "hasho-f1-build/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            f.write(r.read())
    except Exception as e:
        print(f"FAIL {name}: {e}")
        ok = False
        continue
    import csv as _csv
    with open(dest, newline="", encoding="utf-8") as _f:
        header = next(_csv.reader(_f))[0]
    if header != first_col:
        print(f"FAIL {name}: unexpected header: {header[:120]}")
        dest.unlink(missing_ok=True)
        ok = False
    else:
        print(f"OK {name}: {dest.stat().st_size:,} bytes, header: {header[:100]}")
sys.exit(0 if ok else 1)
