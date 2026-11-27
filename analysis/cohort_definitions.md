# Flagship 1 — Cohort definitions (Phase B step 1, 3 Nov 2026)

Locked definitions for the cohort retention analysis. Every number
below was computed from the real loaded star schema
(`data/processed/f1.db`, 112,650 fact rows) with
`sql/01_cohort_sizes.sql` and `sql/02_retention_matrix.sql` — both
verified to execute on that database.

## Definitions (these do not change mid-analysis)

- **Cohort:** a customer's first purchase month. Membership is fixed
  at first purchase and never moves.
- **Customer identity:** `customer_unique_id` via `dim_customer`.
  `customer_id` is near-unique per order (98,666 distinct for 98,666
  orders) and must never be used to count people — doing so would
  falsely show zero repeat buyers.
- **Active in a month:** at least one order in that calendar month.
- **Retention cell (cohort C, month m):** share of cohort C's customers
  active in the m-th month after their first purchase month. Month 0
  is 100% by construction.
- **Churn (Phase C definition, locked here so Phase B stays honest):**
  no purchase in the 6 months following a customer's last observed
  purchase. A customer whose last purchase is within 6 months of the
  dataset end (2018-10-17) is "not yet classifiable", not "churned".
- **Right-censoring (read the matrix honestly):** cohorts from
  Jun 2018 onward have fewer observable months because the dataset
  ends 2018-10-17. Their later cells are missing, not zero — a blank
  is not churn.

## Verified cohort sizes (real data)

- Cohort months: **23** (Sep 2016 – Aug 2018).
- Total customers with at least one fact row: **95,420**
  (dim_customer holds 96,096 unique ids; 676 have no fact row and
  therefore belong to no cohort — noted, not hidden).
- Largest cohort: **Nov 2017, 7,217** new customers (Black Friday
  month — the analysis will test whether that cohort retains worse
  than its neighbours, as discount-acquired cohorts usually do).
- Smallest non-empty cohorts: Sep 2016 (3), Dec 2016 (1) — the
  dataset's first months are a trickle, not a launch.
- **No Nov 2016 cohort exists at all:** zero customers first bought
  in Nov 2016. The matrix carries that month as an empty row, not a
  zero-retention row.
- Repeat buyers: **2,913** unique customers with more than one order
  (2,673 with exactly 2 orders, 192 with 3, 29 with 4, 9 with 5);
  92,507 customers bought exactly once — **96.9% one-time buyers**.
  This is the headline the retention analysis must explain, not
  smooth over.

## What Phase B builds next (5–6 Nov)

The full retention matrix from `sql/02_retention_matrix.sql`
(220 cohort×active-month cells verified to execute), cohort lifetime
value per cohort, and the Nov 2017 vs neighbours comparison. Phase C
then applies the churn definition above to build the at-risk list.
