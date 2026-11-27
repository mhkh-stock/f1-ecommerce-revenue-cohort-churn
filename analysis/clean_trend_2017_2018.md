# Clean 2017–2018 trend — Phase D (12 Nov 2026)

**Question:** what does the monthly revenue trend actually look
like, once the two fake collapses are taken out?

**Answer: strong growth through 2017, then a high plateau in
2018 — not a collapse, and not runaway growth either.** The clean
series is Jan 2017 → Aug 2018 (20 months), restated revenue
(cancelled + unavailable excluded, per the 10 Nov restatement).
It reconciles exactly: clean window BRL 13,449,529.68 + 2016 stub
BRL 44,726.06 + Sep 2018 stub BRL 145.00 = BRL 13,494,400.74,
the published restated headline, over 98,199 orders.

## The two fake collapses (both in the source, not in the load)

1. **November 2016: zero orders.** Settled 11 Nov — the raw Olist
   file holds no November 2016 orders at all. The 2016 stub
   (restated, Q2) is Sep (2 orders, BRL 207.86), Oct (290 orders,
   BRL 44,507.30) and Dec (1 order, BRL 10.90) — BRL 44,726.06
   in total, vs BRL 49,785.92 all-status: the gap is cancelled /
   unavailable orders carrying items.
2. **September 2018: one order.** NEW finding from this step.
   September 2018 holds 16 raw orders — 15 cancelled, 1 shipped
   with items (BRL 145.00). October 2018 holds 4 orders, all
   cancelled, none with items. The Olist extract simply ends at
   the end of August 2018. A chart that ran to Sep 2018 would show
   a −99.98% month-on-month "collapse" that never happened.

**Decision (locked, same rule as 11 Nov):** the trend line is
Jan 2017 → Aug 2018. 2016 and Sep 2018 appear only as labelled
stubs. Any future chart that extends the series must re-check the
tail the same way before adding a month.

## The clean series (restated revenue, BRL)

| Month | Orders | Revenue | MoM | YoY |
|---|---|---|---|---|
| 2017-01 | 787 | 120,098.27 | — | — |
| 2017-02 | 1,718 | 244,959.35 | +103.97% | — |
| 2017-03 | 2,617 | 368,341.32 | +50.37% | — |
| 2017-04 | 2,377 | 353,842.98 | −3.94% | — |
| 2017-05 | 3,640 | 503,159.19 | +42.20% | — |
| 2017-06 | 3,205 | 429,916.61 | −14.56% | — |
| 2017-07 | 3,946 | 492,287.30 | +14.51% | — |
| 2017-08 | 4,272 | 568,245.79 | +15.43% | — |
| 2017-09 | 4,227 | 621,415.91 | +9.36% | — |
| 2017-10 | 4,547 | 660,179.62 | +6.24% | — |
| 2017-11 | 7,421 | 1,003,862.14 | +52.06% | — |
| 2017-12 | 5,618 | 742,183.79 | −26.07% | — |
| 2018-01 | 7,187 | 945,456.29 | +27.39% | +687.24% |
| 2018-02 | 6,624 | 837,895.43 | −11.38% | +242.05% |
| 2018-03 | 7,168 | 981,051.06 | +17.09% | +166.34% |
| 2018-04 | 6,919 | 993,592.98 | +1.28% | +180.80% |
| 2018-05 | 6,833 | 992,871.75 | −0.07% | +97.33% |
| 2018-06 | 6,145 | 863,265.53 | −13.05% | +100.80% |
| 2018-07 | 6,233 | 878,044.27 | +1.71% | +78.36% |
| 2018-08 | 6,421 | 848,860.10 | −3.32% | +49.38% |

Full columns (items, freight, AOV, cumulative) are in
`sql/16_clean_trend_2017_2018.sql` Q1. Every month was verified
twice: SQL vs pure-Python recompute from the raw CSVs
(`src/check_clean_trend.py`, 25 checks, 0 failures).

## What the trend says

1. **2017 is the growth year.** Revenue rises from BRL 120,098
   in Jan 2017 to BRL 742,184 in Dec 2017; the year totals
   BRL 6,108,492.27 over 44,375 orders. The two big jumps are
   real trading events, not noise: Feb (+103.97%, the platform
   ramping from its Jan base) and Nov (+52.06%, Black Friday —
   7,421 orders, the biggest month in the whole dataset).
   December's −26.07% is the normal post-Black-Friday fall, not a
   decline — Dec is still the second-best month of 2017.
2. **2018 is a plateau, not a climb.** Jan–Aug 2018 totals
   BRL 7,341,037.41 over 53,530 orders — bigger than all of 2017
   in eight months — but no month beats Nov 2017's BRL 1,003,862.
   Monthly revenue sits in a BRL 838k–994k band for eight months
   with no upward drift. H1 2018 (BRL 5,614,133.04) is +177.88%
   on H1 2017 (BRL 2,020,317.72), but that is a base effect: H1
   2017 was the ramp.
3. **Year-on-year growth is decelerating.** The YoY column is the
   honest story: Jan 2018 +687.24% (against a 787-order January),
   Feb +242.05%, Mar +166.34%, Apr +180.80%, May +97.33%,
   Jun +100.80%, Jul +78.36%, Aug +49.38%. Growth is real every
   month, but the rate halves across the year. The January figure
   must never be quoted without its base.
4. **Growth is volume, not basket size.** Average order value
   starts at BRL 152.60 (Jan 2017, the highest month) and drifts
   down to a BRL 126–145 band in 2018. Orders grew about 8–9x from
   Jan 2017 (787) to a typical 2018 month (6,145–7,187 orders); AOV
   did not grow at all. Whatever drove the growth brought more
   buyers, not bigger baskets — consistent with Phase B's flat-LTV
   finding (LTV BRL 131–167 per customer across all cohorts).
5. **The peak month is the story's centre.** Nov 2017:
   BRL 1,003,862.14, 7,421 orders, 8,626 items — 16.4% of 2017's
   revenue in one month. It is also the largest cohort (Phase B)
   and the worst-retention cohort (0.55% month-1). The Black
   Friday cohort bought once and never came back — the trend peak
   and the retention problem are the same event.

## What this changes for the executive summary

- Chart the trend Jan 2017 → Aug 2018, with the 2016 and Sep 2018
  stubs labelled, never plotted as trend points.
- Quote H1 2018 vs H1 2017 (+177.88%) only with the base-effect
  warning; quote Aug 2018 YoY (+49.38%) as the current growth rate.
- Never quote Jan 2018's +687.24% YoY on its own.
- The trend supports the recommendations' first line (freight
  pricing on electronics) and third line (retain the 617 at-risk
  repeat buyers): growth is volume-led with flat baskets and
  near-zero retention, so the next real has to come from keeping
  buyers, not from finding more of them.
