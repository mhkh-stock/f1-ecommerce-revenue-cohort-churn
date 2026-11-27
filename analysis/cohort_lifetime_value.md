# Flagship 1 — Cohort lifetime value (Phase B step 3, 6 Nov 2026)

From `sql/09_cohort_lifetime_value.sql`, run on the real star schema
(`data/processed/f1.db`, 112,650 fact rows). Revenue = SUM(price) only;
freight is delivery cost, never revenue. Customers counted by
`customer_unique_id`.

## Verified totals

- Cohort customers sum to **95,420** and cohort revenue sums to
  **BRL 13,591,643.70** — both reconcile exactly to the ingest record.
- Overall lifetime value: **BRL 142.44 per customer**
  (13,591,643.70 / 95,420).

## Findings

1. **LTV is flat across cohorts — the business buys customers, it
   does not grow them.** Per-customer LTV sits in a narrow band
   (BRL 131–167) for every cohort with more than 300 customers,
   from Oct 2016 (BRL 167.07) to Aug 2018 (BRL 133.96). No cohort is
   worth dramatically more than any other; the Nov 2017 Black Friday
   cohort — the largest ever at 7,217 customers and BRL 1,014,927.64
   of revenue — is worth BRL 140.63 per customer, right on the
   average. Size bought revenue, not better customers.
2. **The Nov 2017 discount cohort does NOT retain worse — because
   nothing retains.** Month-1 retention: Oct 2017 0.70%, Nov 2017
   0.55%, Dec 2017 0.22%; month-3: 0.09% / 0.18% / 0.35%. The
   Black Friday hypothesis fails in an interesting way: the expected
   "discount buyers churn faster" gap is invisible because retention
   is near-zero for every cohort. The story is not "Black Friday
   buyers are worse" — it is "almost nobody comes back, whoever they
   are".
3. **Repeat buying is a thin tail, not a base.** Repeat-buyer share
   peaks at 7.29% (Jan 2017 cohort) and falls to 2–4% for most of
   2017–2018. Average orders per customer never exceeds 1.09 in any
   cohort with more than 300 customers.
4. **Read the 2018 cohorts with the censoring warning.** Repeat share
   drops steadily from Mar 2018 (2.46%) to Aug 2018 (0.56%) — but
   those customers simply had less calendar time before the dataset
   ends (2018-10-17) to make a second purchase. That decline is a
   measurement artefact, not a worsening business. The honest
   comparison set is cohorts up to Dec 2017, which had a full year
   or more of observable follow-up.

## What this means for Phase C (churn) and Phase D (recommendations)

- Churn here is not "customers drifting away over months" — it is
  "customers who never return after the first order". The churn
  definition (no purchase in 6 months after last purchase) will
  classify ~97% of customers as churned; Phase C must report that
  plainly and focus the at-risk list on the small repeat-buyer tail
  that is actually saveable.
- The margin story from Phase A (freight 16.6% of price, 4,119 items
  where freight exceeds price) matters more than any retention lever:
  with LTV flat and retention near-zero, the three recommendations in
  Phase D should lead with acquisition economics and freight, not
  with loyalty programmes for customers who do not return.

## Phase B status: COMPLETE

Cohort definitions + sizes (3 Nov) → retention matrix shape (3 Nov)
→ freight-by-category cross-tab (5 Nov) → cohort lifetime value
+ Nov 2017 comparison (6 Nov). Phase C (RFM + churn) starts 7–8 Nov
per the execution plan.
