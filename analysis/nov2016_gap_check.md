# November 2016 gap check — Phase D (11 Nov 2026)

**Question:** the cohort analysis found 23 cohorts but none for
Nov 2016 (Sep 2016, Oct 2016, then Dec 2016). Is November 2016 a
hole in our load, or is it genuinely absent from the source?

**Answer: the gap is in the source.** The raw Olist orders file
itself contains **zero orders with a purchase timestamp in
November 2016** — no orders, no items, no revenue. Nothing was
lost in the ingest; there is nothing to load.

## What 2016 actually looks like

| Month | Raw orders | Item-bearing orders | Items | Revenue (BRL) |
|---|---|---|---|---|
| 2016-09 | 4 | 3 | 6 | 267.36 |
| 2016-10 | 324 | 308 | 363 | 49,507.66 |
| 2016-11 | **0** | **0** | **0** | **0.00** |
| 2016-12 | 1 | 1 | 1 | 10.90 |
| **2016 total** | **329** | **312** | **370** | **49,785.92** |

- **Sep 2016** is 4 orders on 4, 5, 13 and 15 Sep (2 cancelled,
  1 shipped, 1 delivered; the 13 Sep order is cancelled with no
  items, so only 3 orders reach the fact table).
- **Oct 2016** is a one-week pilot: item-bearing purchases span
  2–10 Oct only. One more order exists on 22 Oct — cancelled,
  no items. 16 of the 324 October orders carry no items at all.
- **Dec 2016** is exactly one order, 23 Dec, delivered, 1 item,
  BRL 10.90.
- **Jan 2017** is the first normal month: 800 raw orders, 789
  item-bearing, BRL 120,312.87 — and volume never drops back to
  2016 levels again.

The whole of 2016 is 329 orders and BRL 49,785.92 — **0.37% of
the dataset's BRL 13,591,643.70 revenue**. It is a pilot fragment,
not a trading year.

## Two load facts this check also settled

1. **`dim_date` is a presence spine of the orders file, not of
   the fact table.** It holds 634 rows = the 634 distinct purchase
   dates in the raw orders file. The fact table covers 616 of
   them; the other 18 are dates whose orders all lack items
   (13 Sep 2016, 22 Oct 2016, and 16 dates in the Aug–Oct 2018
   tail). Any month-spine query must therefore generate its own
   months explicitly — joining to `dim_date` alone silently drops
   empty months, exactly as it dropped November 2016.
2. **Cancelled orders can carry items.** The 2 Oct 2016 order is
   cancelled yet has 1 item in the fact table. This is consistent
   with the order-status restatement (10 Nov): 467
   cancelled/unavailable orders carry items. The fact table is
   item-grain, not status-filtered — status filtering belongs in
   the query, never assumed in the load.

## Decision for the flagship (locked)

- **Monthly trend charts start Jan 2017.** A chart that begins
  Sep 2016 (3 orders), Oct (308), Nov (0), Dec (1) would read as
  a collapse and a recovery that never happened. The clean series
  is Jan 2017 → Sep 2018.
- **2016 is shown only as a labelled stub:** one footnote line in
  the executive summary and the README — "2016 is a 329-order
  pilot fragment (BRL 49,785.92, 0.37% of revenue) with no orders
  at all in November 2016; the analysed series starts Jan 2017."
  Never plotted, never averaged into a 2016 monthly mean.
- **The three micro-cohorts stay in the retention matrix.**
  Sep 2016 (3 customers), Oct 2016 (305) and Dec 2016 (1) are
  real customers with real first purchases; removing them would
  change the 95,420-customer total. They are flagged in the
  matrix footnote as too small to read retention from — the
  Oct 2016 cohort (305 customers) is the only one of the three
  large enough to quote.
- **No re-ingest, no patch.** The load is correct; the source is
  sparse. Filling November 2016 with anything would be inventing
  data.

## Verification

`sql/15_nov2016_gap_check.sql` + `src/check_nov2016_gap.py` —
**26 checks, 0 failures.** Every monthly number is produced twice
(SQL on the read-only star + pure-Python recompute from the raw
CSVs) and the two paths agree to the cent; the raw-file counts
(Sep 4 / Oct 324 / Nov 0 / Dec 1 orders) are counted straight
from `olist_orders_dataset.csv`.

Remaining Phase D: clean 2017–2018 trend (monthly series from
Jan 2017, with the 2016 stub above as its footnote).
