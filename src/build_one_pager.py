#!/usr/bin/env python3
"""Build the Flagship 1 one-pager PDF (exactly 1 page, A4).

Every number is read from powerbi/verified_measures.json or hard-coded
only where the value is a verified analysis-note figure (with its
source named in the footer). Run: python3 src/build_one_pager.py
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "one_pager.pdf"

with open(ROOT / "powerbi" / "verified_measures.json") as f:
    M = json.load(f)

BRL = lambda v: f"BRL {v:,.2f}"

TITLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=17,
                       leading=20, textColor=colors.HexColor("#1a2a4a"))
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9,
                     leading=12, textColor=colors.HexColor("#44546a"))
HEADLINE = ParagraphStyle("headline", fontName="Helvetica-Bold",
                          fontSize=10, leading=13.5,
                          textColor=colors.HexColor("#1a2a4a"))
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11,
                    leading=13, textColor=colors.HexColor("#1a2a4a"),
                    spaceBefore=7, spaceAfter=3)
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=8.6,
                      leading=11.4, textColor=colors.HexColor("#222222"),
                      spaceAfter=3)
SMALL = ParagraphStyle("small", fontName="Helvetica", fontSize=7.6,
                       leading=10, textColor=colors.HexColor("#333333"))
KPI_NUM = ParagraphStyle("kpinum", fontName="Helvetica-Bold", fontSize=13,
                         leading=15, textColor=colors.HexColor("#1a2a4a"),
                         alignment=1)
KPI_LBL = ParagraphStyle("kpilbl", fontName="Helvetica", fontSize=7.6,
                         leading=9.5, textColor=colors.HexColor("#44546a"),
                         alignment=1)
CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.2,
                      leading=10.5, textColor=colors.HexColor("#222222"))
CELL_R = ParagraphStyle("cellr", parent=CELL, alignment=2)
CELL_H = ParagraphStyle("cellh", parent=CELL, fontName="Helvetica-Bold",
                        textColor=colors.white)

kpis = [
    (BRL(M["total_revenue_restated"]), "Revenue (restated)"),
    (f"{M['total_orders_restated']:,}", "Orders (restated)"),
    (f"{M['total_customers_restated']:,}", "Customers (restated)"),
    (f"{M['churn_rate_restated']:.2f}%", "Churned"),
]

kpi_table = Table(
    [[Paragraph(n, KPI_NUM), ] for n, _ in kpis],
    colWidths=[(A4[0] - 72) / 4.0] * 4,
)
kpi_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef2f7")),
    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#1a2a4a")),
    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c4d4")),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
]))
kpi_lbls = Table(
    [[Paragraph(lbl, KPI_LBL) for _, lbl in kpis]],
    colWidths=[(A4[0] - 72) / 4.0] * 4,
)
kpi_lbls.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef2f7")),
    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#1a2a4a")),
    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c4d4")),
    ("TOPPADDING", (0, 0), (-1, -1), 1),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))

rows = [
    ("Average order value (restated)", BRL(M["avg_order_value_restated"])),
    ("Freight — delivery cost (restated)",
     f"{BRL(M['total_freight_restated'])} · {M['freight_pct_revenue_restated']:.2f}% of price"),
    ("Items costing more to deliver than they sell for",
     f"{M['items_over_100pct_freight_restated']:,} (3.6%)"),
    ("One-time buyers", "92,096 of 94,983 (97.0%)"),
    ("Lifetime value per customer",
     f"BRL {M['avg_spend_per_customer_restated']:.2f} (BRL 131–163 by cohort)"),
    ("Saveable at-risk revenue", "BRL 168,541.14 (611 repeat buyers)"),
    ("São Paulo share of revenue",
     f"{M['sp_revenue_share_restated']:.2f}% (top 3 states 63.35%)"),
    ("Peak month", "Nov 2017 — BRL 1,003,862.14, 7,421 orders"),
    ("Growth", "Aug 2018 YoY +49.38% — decelerating through 2018"),
]
tdata = [[Paragraph("Number", CELL_H), Paragraph("Value", CELL_H)]]
tdata += [[Paragraph(a, CELL), Paragraph(b, CELL_R)] for a, b in rows]
num_table = Table(tdata, colWidths=[270, A4[0] - 72 - 270])
num_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2a4a")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
     [colors.white, colors.HexColor("#f2f5f9")]),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c4d4")),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
]))

story = [
    Paragraph("Olist E-commerce — Revenue, Cohort &amp; Churn", TITLE),
    Paragraph("Flagship 1 · One-pager · 21 Nov 2026 · Real Olist data, "
              "112,650 order items · Sep 2016 – Aug 2018", SUB),
    Spacer(1, 4),
    HRFlowable(width="100%", thickness=1.2,
               color=colors.HexColor("#1a2a4a")),
    Spacer(1, 5),
    Paragraph("Olist earned <b>BRL 13,494,400.74</b> from <b>94,983 "
              "customers</b> across <b>98,199 orders</b>, but it buys "
              "customers it does not keep — <b>97.0% buy once</b>, "
              "lifetime value is flat at about <b>BRL 142</b> per "
              "customer, and <b>69.99% have churned</b> — so the margin "
              "is in freight and geography, not in loyalty.", HEADLINE),
    Spacer(1, 5),
    kpi_table,
    kpi_lbls,
    Paragraph("The three findings", H2),
    Paragraph("<b>1. Revenue is real but leaky.</b> Freight eats 16.64% "
              "of every real of price. The leak is concentrated in "
              "electronics — 29.50% freight (restated), 22.18% of its "
              "items cost more to deliver than they sell for — not "
              "spread across the catalogue, so it is fixable without "
              "touching product prices.", BODY),
    Paragraph("<b>2. Customers are bought, not kept.</b> Lifetime value "
              "sits in a narrow BRL 131–163 band for every cohort with "
              "more than 300 customers, including the Nov 2017 Black "
              "Friday cohort (7,188 customers, BRL 140.30 each). "
              "Month-1 retention is 0.56% for that cohort and 0.71% for "
              "its neighbour: the discount-buyer hypothesis fails "
              "because nothing retains.", BODY),
    Paragraph("<b>3. Growth is volume, not basket size — and it is "
              "slowing.</b> Orders grew about 8–9x from Jan 2017 (787) "
              "to a typical 2018 month (6,145–7,187 orders); average "
              "order value did not grow at all. YoY growth decelerates "
              "across 2018 (+242% in Feb to +49% in Aug). The peak "
              "month and the retention problem are the same event: the "
              "Black Friday cohort bought once and never came back.",
              BODY),
    Paragraph("The three moves", H2),
    Paragraph("<b>1. Fix freight pricing on electronics first</b> — "
              "category-level delivery pricing (minimum order value / "
              "surcharge on low-price electronics). Worth roughly "
              "BRL 350,000 across a dataset this size; freight share "
              "from 16.6% toward ~14%.", BODY),
    Paragraph("<b>2. Grow acquisition outside São Paulo</b> — shift "
              "marginal spend to RJ and MG first; LTV is flat "
              "everywhere, so the test is which state acquires "
              "cheapest. Target: SP share below 35% while total "
              "revenue grows.", BODY),
    Paragraph("<b>3. Retain the 611 at-risk repeat buyers only</b> — "
              "win-back offers to those 611 people (BRL 168,541.14). "
              "Never a broad campaign to all 18,536 at-risk customers: "
              "the bigger number (BRL 2.73M) is one-time revenue that "
              "was never going to repeat.", BODY),
    Paragraph("The numbers", H2),
    num_table,
    Spacer(1, 6),
    Paragraph("Read this before quoting any number — <b>Restated "
              "headline:</b> as loaded (all statuses) revenue is "
              "BRL 13,591,643.70; the restatement is only −0.72%. "
              "<b>Data window:</b> clean trend Jan 2017 → Aug 2018; "
              "Nov 2016 has zero orders in the source and Sep 2018 is "
              "a 1-order stub (16 raw orders, 15 cancelled, BRL 145.00) "
              "— neither is a trend point. <b>Two unrelated 611s:</b> "
              "electronics items over 100% freight = 611 items; "
              "at-risk repeat buyers = 611 people — never mix them. "
              "<b>Power BI:</b> model, 12 DAX measures and page layouts "
              "built and verified; the .pbix is NOT YET BUILT (needs "
              "Power BI Desktop on Windows). <b>Sources:</b> sql/03–"
              "sql/16, src/check_*.py (full regression sweep "
              "21 Nov 2026). Revenue = SUM(price); freight is delivery "
              "cost, never revenue; customers by customer_unique_id.",
              SMALL),
]

doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                        leftMargin=36, rightMargin=36,
                        topMargin=32, bottomMargin=28,
                        title="Flagship 1 — One-pager",
                        author="Muhammad Hashir")
doc.build(story)
print(f"Wrote {OUT}")
