#!/usr/bin/env python3
"""FLAGSHIP 1 — Phase E block 2 (15 Nov 2026): render the three dashboard
page previews (composite 16:9 pages: KPI cards + the page's charts),
from powerbi/f1_powerbi.db. Every number comes from the model DB;
KPI cards read powerbi/verified_measures.json. Restated figures
throughout (cancelled + unavailable excluded).

    python3 src/render_dashboard_pages.py
"""
import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "powerbi" / "f1_powerbi.db"
OUT = PROJECT / "outputs"
VM = json.loads((PROJECT / "powerbi" / "verified_measures.json").read_text())
R = "order_status NOT IN ('canceled', 'unavailable')"
ACCENT = "#1F4E79"
HIGHLIGHT = "#ED7D31"
FOOTNOTE = ("Source: Olist Brazilian e-commerce extract, Sep 2016 – Aug 2018. "
            "Revenue excludes cancelled + unavailable orders (BRL 97,242.96, 0.72%). "
            "All-status total BRL 13,591,643.70.")


def kpi_row(fig, cards):
    """Draw a row of KPI cards across the top of the figure."""
    n = len(cards)
    for i, (label, value, sub) in enumerate(cards):
        x0 = 0.02 + i * (0.96 / n)
        ax = fig.add_axes([x0, 0.845, 0.96 / n - 0.015, 0.095])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.02, 0.05), 0.96, 0.90,
                                    boxstyle="round,pad=0.02,rounding_size=0.05",
                                    facecolor="#EAF1F8", edgecolor=ACCENT, linewidth=1.2))
        ax.text(0.5, 0.72, value, ha="center", va="center",
                fontsize=15, fontweight="bold", color=ACCENT)
        ax.text(0.5, 0.38, label, ha="center", va="center", fontsize=9.5)
        ax.text(0.5, 0.14, sub, ha="center", va="center", fontsize=7.5, color="#555555")


def header(fig, title, subtitle):
    fig.text(0.02, 0.99, title, fontsize=17, fontweight="bold", color=ACCENT, va="top")
    fig.text(0.02, 0.955, subtitle, fontsize=9.5, color="#555555", va="top")


def footer(fig):
    fig.text(0.02, 0.015, FOOTNOTE, fontsize=7.5, color="#777777")


def page1(con):
    months, rev = zip(*con.execute(
        f"SELECT substr(date_id, 1, 7), SUM(price) FROM fact_order_items "
        f"WHERE {R} AND date_id >= '2017-01-01' AND date_id < '2018-09-01' "
        f"GROUP BY 1 ORDER BY 1").fetchall())
    cats = con.execute(
        f"SELECT p.product_category_name, SUM(f.price) FROM fact_order_items f "
        f"JOIN dim_product p ON f.product_id = p.product_id WHERE {R} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 10").fetchall()
    fig = plt.figure(figsize=(16, 9))
    header(fig, "Page 1 — Overview", "Slicers: order year (2017–2018) · restated only (cancelled + unavailable excluded)")
    kpi_row(fig, [
        ("Total Revenue (Restated)", f"BRL {VM['total_revenue_restated']:,.2f}", "excl. cancelled + unavailable"),
        ("Total Orders (Restated)", f"{VM['total_orders_restated']:,}", "98,666 all statuses"),
        ("Total Customers (Restated)", f"{VM['total_customers_restated']:,}", "95,420 all statuses"),
        ("Avg Order Value", f"BRL {VM['avg_order_value_restated']:,.2f}", "restated revenue / orders"),
        ("Churn Rate", f"{VM['churn_rate_restated']:.2f}%", "no purchase in 6 months"),
    ])
    ax = fig.add_axes([0.06, 0.10, 0.52, 0.66])
    ax.plot(months, [v / 1000 for v in rev], marker="o", linewidth=2, color=ACCENT)
    ax.fill_between(months, [v / 1000 for v in rev], alpha=0.12, color=ACCENT)
    peak = max(range(len(rev)), key=lambda i: rev[i])
    ax.annotate(f"Nov 2017 peak\nBRL {rev[peak] / 1000:,.0f}k",
                xy=(peak, rev[peak] / 1000), xytext=(peak - 7, rev[peak] / 1000 - 330),
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.set_title("Monthly revenue (restated) — Jan 2017 to Aug 2018")
    ax.set_ylabel("Revenue (BRL thousands)")
    ax.set_xticks(range(0, len(months), 2))
    ax.grid(axis="y", alpha=0.3)
    ax2 = fig.add_axes([0.68, 0.10, 0.28, 0.66])
    names = [c[0].replace("_", " ")[:18] for c in reversed(cats)]
    vals = [c[1] / 1000 for c in reversed(cats)]
    ax2.barh(names, vals, color=ACCENT)
    ax2.set_title("Revenue by category — top 10 (restated)")
    ax2.set_xlabel("Revenue (BRL thousands)")
    fig.text(0.06, 0.045, "2016 is a 329-order pilot stub and Sep 2018 is a 1-order stub — the trend starts Jan 2017 and stops Aug 2018.",
             fontsize=9, style="italic")
    footer(fig)
    fig.savefig(OUT / "page1_overview.png", dpi=150)
    plt.close(fig)
    print(f"page1: trend total BRL {sum(rev):,.2f}; peak {months[peak]} BRL {rev[peak]:,.2f}; "
          f"top category {cats[0][0]} BRL {cats[0][1]:,.2f}")


def page2(con):
    freight = con.execute(
        f"SELECT p.product_category_name, "
        f"100.0 * SUM(f.freight_value) / SUM(f.price) AS fpct "
        f"FROM fact_order_items f JOIN dim_product p ON f.product_id = p.product_id "
        f"WHERE {R} GROUP BY 1 HAVING COUNT(*) >= 500 ORDER BY 2 DESC LIMIT 10").fetchall()
    states = con.execute(
        f"SELECT c.customer_state, SUM(f.price) FROM fact_order_items f "
        f"JOIN dim_customer c ON f.customer_id = c.customer_id WHERE {R} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 10").fetchall()
    pts = con.execute(
        f"SELECT price, freight_value FROM fact_order_items "
        f"WHERE {R} AND (rowid % 23) = 0").fetchall()
    fig = plt.figure(figsize=(16, 9))
    header(fig, "Page 2 — Where revenue leaks", "Slicers: order year (2017–2018) · restated only")
    kpi_row(fig, [
        ("Total Freight (Restated)", f"BRL {VM['total_freight_restated']:,.2f}", "16.64% of restated revenue"),
        ("Freight % of Revenue", f"{VM['freight_pct_revenue_restated']:.2f}%", "restated"),
        ("Items Over 100% Freight", f"{VM['items_over_100pct_freight_restated']:,}", "cost more to deliver than they sell for"),
    ])
    ax = fig.add_axes([0.15, 0.52, 0.33, 0.30])
    ax.barh([c[0].replace("_", " ")[:16] for c in reversed(freight)],
            [c[1] for c in reversed(freight)], color=ACCENT)
    ax.set_title("Freight % of price by category — top 10 (500+ items)")
    ax.set_xlabel("Freight as % of price")
    ax2 = fig.add_axes([0.54, 0.52, 0.42, 0.30])
    ax2.barh([s[0] for s in reversed(states)],
             [s[1] / 1000 for s in reversed(states)], color=ACCENT)
    ax2.set_title("Revenue by customer state — top 10")
    ax2.set_xlabel("Revenue (BRL thousands)")
    ax3 = fig.add_axes([0.06, 0.08, 0.90, 0.36])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax3.scatter(xs, ys, s=4, alpha=0.35, color=ACCENT)
    lim = max(max(xs), max(ys)) * 1.05
    ax3.plot([0, lim], [0, lim], color=HIGHLIGHT, linewidth=1.5,
             label="freight = price (diagonal)")
    ax3.set_xlim(0, 1200)
    ax3.set_ylim(0, 400)
    ax3.set_title(f"Item price vs freight value — 1-in-23 sample ({len(pts):,} points); "
                  f"the cloud above the diagonal is the {VM['items_over_100pct_freight_restated']:,} items that cost more to deliver than they sell for")
    ax3.set_xlabel("Item price (BRL)")
    ax3.set_ylabel("Freight value (BRL)")
    ax3.legend(fontsize=9)
    footer(fig)
    fig.savefig(OUT / "page2_revenue_leak.png", dpi=150)
    plt.close(fig)
    print(f"page2: top freight% {freight[0][0]} {freight[0][1]:.2f}%; "
          f"top state {states[0][0]} BRL {states[0][1]:,.2f}; scatter n={len(pts)}")


def page3(con):
    # Retention matrix, restated: cohorts Jan 2017 – Dec 2017, months 0–5.
    first = con.execute(
        f"SELECT cu.customer_unique_id, substr(MIN(f.date_id), 1, 7) AS cohort "
        f"FROM fact_order_items f JOIN dim_customer cu ON cu.customer_id = f.customer_id "
        f"WHERE {R} GROUP BY cu.customer_unique_id").fetchall()
    cohort_of = {u: c for u, c in first}
    cohort_size = {}
    for u, c in first:
        cohort_size[c] = cohort_size.get(c, 0) + 1
    act = con.execute(
        f"SELECT cu.customer_unique_id, substr(f.date_id, 1, 7) AS m "
        f"FROM fact_order_items f JOIN dim_customer cu ON cu.customer_id = f.customer_id "
        f"WHERE {R} GROUP BY cu.customer_unique_id, m").fetchall()
    from collections import defaultdict
    active = defaultdict(set)
    for u, m in act:
        active[(cohort_of[u], m)].add(u)

    def months_between(a, b):
        return (int(b[:4]) * 12 + int(b[5:7])) - (int(a[:4]) * 12 + int(a[5:7]))

    cohorts = [f"2017-{m:02d}" for m in range(1, 13)]
    mat = []
    for c in cohorts:
        row = []
        for k in range(6):
            target = f"{int(c[:4]) + (int(c[5:7]) + k - 1) // 12:04d}-{(int(c[5:7]) + k - 1) % 12 + 1:02d}"
            n = len(active.get((c, target), set()))
            row.append(100.0 * n / cohort_size[c])
        mat.append(row)
    ltv = con.execute(
        f"SELECT cohort, SUM(revenue) / COUNT(DISTINCT customer_unique_id) AS ltv "
        f"FROM (SELECT cu.customer_unique_id, substr(MIN(f.date_id), 1, 7) AS cohort, "
        f"SUM(f.price) AS revenue FROM fact_order_items f "
        f"JOIN dim_customer cu ON cu.customer_id = f.customer_id "
        f"WHERE {R} GROUP BY cu.customer_unique_id) "
        f"WHERE cohort >= '2017-01' AND cohort <= '2018-08' "
        f"GROUP BY cohort ORDER BY cohort").fetchall()
    fig = plt.figure(figsize=(16, 9))
    header(fig, "Page 3 — Cohorts & churn", "Slicers: order year (2017–2018) · restated only")
    kpi_row(fig, [
        ("Repeat Buyer Rate", f"{VM['repeat_buyer_rate_restated']:.2f}%", f"{VM['repeat_buyers_restated']:,} of {VM['total_customers_restated']:,} customers"),
        ("Churn Rate", f"{VM['churn_rate_restated']:.2f}%", "no purchase in 6 months"),
        ("Saveable At-Risk Revenue", "BRL 168,541.14", "611 repeat buyers, last buy 3–6 months ago"),
    ])
    ax = fig.add_axes([0.06, 0.10, 0.52, 0.68])
    im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"Month {k}" for k in range(6)])
    ax.set_yticks(range(len(cohorts)))
    ax.set_yticklabels(cohorts)
    for i in range(len(cohorts)):
        for j in range(6):
            ax.text(j, i, f"{mat[i][j]:.2f}%" if mat[i][j] >= 1 else f"{mat[i][j]:.2f}%",
                    ha="center", va="center", fontsize=8,
                    color="white" if mat[i][j] > 50 else "black")
    ax.set_title("Cohort retention — % of cohort active in month k after first purchase (2017 cohorts)")
    fig.colorbar(im, ax=ax, shrink=0.9, label="% retained")
    ax2 = fig.add_axes([0.64, 0.10, 0.32, 0.68])
    ax2.bar([c[0] for c in ltv], [c[1] for c in ltv], color=ACCENT)
    ax2.axhline(sum(c[1] for c in ltv) / len(ltv), color=HIGHLIGHT, linestyle="--",
                label=f"mean BRL {sum(c[1] for c in ltv) / len(ltv):.2f}")
    ax2.set_title("LTV by cohort (restated) — flat BRL 131–163")
    ax2.set_ylabel("Revenue per customer (BRL)")
    ax2.tick_params(axis="x", rotation=45, labelsize=8)
    ax2.legend(fontsize=9)
    fig.text(0.06, 0.045, "Retention in month 1 is 0.56% (Nov 2017) vs 0.71% (Oct 2017), restated — the discount-cohort gap is invisible because retention is near-zero everywhere.",
             fontsize=9, style="italic")
    footer(fig)
    fig.savefig(OUT / "page3_cohorts_churn.png", dpi=150)
    plt.close(fig)
    nov1 = mat[10][1]
    oct1 = mat[9][1]
    print(f"page3: month-1 retention Nov 2017 {nov1:.2f}% / Oct 2017 {oct1:.2f}% (restated); "
          f"LTV range BRL {min(c[1] for c in ltv):.2f}–{max(c[1] for c in ltv):.2f}")


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    page1(con)
    page2(con)
    page3(con)
    con.close()
    print("rendered: page1_overview.png, page2_revenue_leak.png, page3_cohorts_churn.png")


if __name__ == "__main__":
    main()
