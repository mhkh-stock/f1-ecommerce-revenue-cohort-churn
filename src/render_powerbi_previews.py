#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase E (14 Nov 2026): render the Power BI preview charts.

Matplotlib renders of the same numbers the dashboard will show, so
the model is proven before anyone opens Power BI Desktop. All four
charts use RESTATED figures (cancelled + unavailable excluded) from
`powerbi/f1_powerbi.db`, and the trend follows the sql/16 clean-trend
rule: Jan 2017 → Aug 2018, with the 2016 pilot stub and the Sep 2018
1-order stub left off the axis (noted in the caption).

    python3 src/render_powerbi_previews.py
"""
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "powerbi" / "f1_powerbi.db"
OUT = PROJECT / "outputs"
R = "order_status NOT IN ('canceled', 'unavailable')"

plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#555555"})


def monthly_revenue(con):
    rows = con.execute(
        f"SELECT substr(date_id, 1, 7) m, SUM(price) rev, "
        f"COUNT(DISTINCT order_id) orders FROM fact_order_items "
        f"WHERE {R} AND date_id >= '2017-01-01' AND date_id < '2018-09-01' "
        f"GROUP BY 1 ORDER BY 1").fetchall()
    months = [r[0] for r in rows]
    rev = [r[1] / 1000 for r in rows]  # BRL thousands
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(months, rev, marker="o", linewidth=2)
    ax.fill_between(months, rev, alpha=0.12)
    peak = max(range(len(rev)), key=lambda i: rev[i])
    ax.annotate(f"Nov 2017 peak\nBRL {rev[peak]:,.0f}k",
                xy=(peak, rev[peak]), xytext=(peak - 7, rev[peak] - 330),
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.set_title("Monthly revenue (restated) — Jan 2017 to Aug 2018")
    ax.set_ylabel("Revenue (BRL thousands)")
    ax.set_xticks(range(0, len(months), 2))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "preview_monthly_revenue.png", dpi=150)
    plt.close(fig)
    return months, rev


def revenue_by_category(con):
    rows = con.execute(
        f"SELECT p.product_category_name, SUM(f.price) rev "
        f"FROM fact_order_items f JOIN dim_product p "
        f"ON f.product_id = p.product_id WHERE {R} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 10").fetchall()
    cats = [r[0].replace("_", " ") for r in reversed(rows)]
    rev = [r[1] / 1000 for r in reversed(rows)]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.barh(cats, rev)
    for i, v in enumerate(rev):
        ax.text(v + 15, i, f"BRL {v:,.0f}k", va="center", fontsize=9)
    ax.set_title("Revenue by product category — top 10 (restated)")
    ax.set_xlabel("Revenue (BRL thousands)")
    ax.set_xlim(0, max(rev) * 1.18)
    fig.tight_layout()
    fig.savefig(OUT / "preview_revenue_by_category.png", dpi=150)
    plt.close(fig)
    return rows


def revenue_by_state(con):
    rows = con.execute(
        f"SELECT c.customer_state, SUM(f.price) rev "
        f"FROM fact_order_items f JOIN dim_customer c "
        f"ON f.customer_id = c.customer_id WHERE {R} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 10").fetchall()
    states = [r[0] for r in reversed(rows)]
    rev = [r[1] / 1000 for r in reversed(rows)]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.barh(states, rev)
    for i, v in enumerate(rev):
        ax.text(v + 60, i, f"BRL {v:,.0f}k", va="center", fontsize=9)
    ax.set_title("Revenue by customer state — top 10 (restated, SP 38.27%)")
    ax.set_xlabel("Revenue (BRL thousands)")
    ax.set_xlim(0, max(rev) * 1.15)
    fig.tight_layout()
    fig.savefig(OUT / "preview_revenue_by_state.png", dpi=150)
    plt.close(fig)
    return rows


def freight_by_category(con):
    rows = con.execute(
        f"SELECT p.product_category_name, "
        f"100.0 * SUM(f.freight_value) / SUM(f.price) pct, "
        f"SUM(CASE WHEN f.freight_value > f.price THEN 1 ELSE 0 END) over100 "
        f"FROM fact_order_items f JOIN dim_product p "
        f"ON f.product_id = p.product_id WHERE {R} "
        f"GROUP BY 1 HAVING COUNT(*) >= 500 ORDER BY 2 DESC LIMIT 10").fetchall()
    cats = [r[0].replace("_", " ") for r in reversed(rows)]
    pct = [r[1] for r in reversed(rows)]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.barh(cats, pct)
    for i, v in enumerate(pct):
        ax.text(v + 0.4, i, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_title("Freight as % of price by category — top 10 (restated, "
                "categories with 500+ items)")
    ax.set_xlabel("Freight / price (%)")
    ax.set_xlim(0, max(pct) * 1.18)
    fig.tight_layout()
    fig.savefig(OUT / "preview_freight_by_category.png", dpi=150)
    plt.close(fig)
    return rows


def main() -> int:
    if not DB.exists():
        print("ERROR: model database missing — run powerbi/build_model.py first")
        return 1
    OUT.mkdir(exist_ok=True)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    m, r = monthly_revenue(con)
    print(f"monthly revenue: {len(m)} months, "
          f"total BRL {sum(r) * 1000:,.2f}")
    revenue_by_category(con)
    revenue_by_state(con)
    freight_by_category(con)
    con.close()
    for name in ("preview_monthly_revenue.png",
                 "preview_revenue_by_category.png",
                 "preview_revenue_by_state.png",
                 "preview_freight_by_category.png"):
        p = OUT / name
        print(f"  {name}: {p.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
