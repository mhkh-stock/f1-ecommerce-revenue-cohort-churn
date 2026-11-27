"""FLAGSHIP 1 — ingest loader (step 2a, 1 Nov 2026).

Loads Olist-shaped CSVs into the star schema in ../sql/schema.sql.
Staging first, then star — nothing lands in fact_order_items without
passing the checks below. Run:

    python3 src/ingest.py --source-dir <csv folder> --db data/processed/f1.db

Expected source files (public Olist Brazilian e-commerce names):
customers, products, sellers, orders, order_items. Only the columns
the star schema needs are read; extra Olist columns are ignored.

DQ rules (all counted and reported, never silent):
- rows with a missing key (customer/product/seller) are rejected;
- items priced below 0 are rejected (schema CHECK would also block them);
- order items whose order timestamp is missing get no dim_date row
  and are rejected;
- rejected rows are listed in the report with their reason.

This loader was tested 1 Nov 2026 on a tiny synthetic fixture
(3 customers, 2 products, 1 seller, 4 items incl. 1 negative-price
item and 1 orphan item) — the fixture is NOT Olist data and is NOT
shipped in data/. The real Olist load runs Mon 2 Nov 2026 and its
counts replace the fixture numbers in the README.
"""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCHEMA = BASE / "sql" / "schema.sql"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    src = Path(args.source_dir)
    db = Path(args.db)
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()

    customers = read_csv(src / "olist_customers_dataset.csv")
    products = read_csv(src / "olist_products_dataset.csv")
    sellers = read_csv(src / "olist_sellers_dataset.csv")
    orders = read_csv(src / "olist_orders_dataset.csv")
    items = read_csv(src / "olist_order_items_dataset.csv")

    con = sqlite3.connect(db)
    con.executescript(SCHEMA.read_text())
    con.execute("PRAGMA foreign_keys = ON")

    con.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?,?)",
        [(c["customer_id"], c["customer_unique_id"],
          c.get("customer_state", ""), c.get("customer_city", "")) for c in customers],
    )
    con.executemany(
        "INSERT INTO dim_product VALUES (?,?,?,?,?,?)",
        [(p["product_id"], p.get("product_category_name", ""),
          _f(p.get("product_weight_g")), _f(p.get("product_length_cm")),
          _f(p.get("product_height_cm")), _f(p.get("product_width_cm")))
         for p in products],
    )
    con.executemany(
        "INSERT INTO dim_seller VALUES (?,?,?)",
        [(s["seller_id"], s.get("seller_state", ""), s.get("seller_city", ""))
         for s in sellers],
    )
    order_date = {}
    for o in orders:
        ts = o.get("order_purchase_timestamp", "")[:10]
        if ts:
            order_date[o["order_id"]] = ts
    for d in sorted(set(order_date.values())):
        y, m, _ = (int(x) for x in d.split("-"))
        con.execute("INSERT INTO dim_date VALUES (?,?,?,?)",
                    (d, y, m, (m - 1) // 3 + 1))

    rejected = []
    kept = 0
    cust_ids = {c["customer_id"] for c in customers}
    prod_ids = {p["product_id"] for p in products}
    sell_ids = {s["seller_id"] for s in sellers}
    order_customer = {o["order_id"]: o["customer_id"] for o in orders}
    for it in items:
        oid = it["order_id"]
        reason = None
        if order_customer.get(oid) not in cust_ids:
            reason = "unknown customer"
        elif it["product_id"] not in prod_ids:
            reason = "unknown product"
        elif it["seller_id"] not in sell_ids:
            reason = "unknown seller"
        elif oid not in order_date:
            reason = "missing order date"
        elif _f(it.get("price")) is None or _f(it.get("price")) < 0:
            reason = "bad price"
        if reason:
            rejected.append((oid, it.get("order_item_id"), reason))
            continue
        con.execute(
            "INSERT INTO fact_order_items VALUES (?,?,?,?,?,?,?,?)",
            (oid, int(it["order_item_id"]), order_customer[oid],
             it["product_id"], it["seller_id"], order_date[oid],
             _f(it.get("price")), _f(it.get("freight_value")) or 0.0),
        )
        kept += 1
    con.commit()

    counts = {
        "dim_customer": con.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0],
        "dim_product": con.execute("SELECT COUNT(*) FROM dim_product").fetchone()[0],
        "dim_seller": con.execute("SELECT COUNT(*) FROM dim_seller").fetchone()[0],
        "dim_date": con.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0],
        "fact_order_items": con.execute("SELECT COUNT(*) FROM fact_order_items").fetchone()[0],
    }
    con.close()
    print(f"loaded {db}")
    print("counts:", counts)
    print(f"items kept={kept} rejected={len(rejected)}")
    for r in rejected:
        print("  rejected:", r)
    return 0


def _f(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    sys.exit(main())
