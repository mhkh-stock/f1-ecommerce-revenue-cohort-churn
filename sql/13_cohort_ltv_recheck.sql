-- Flagship 1, Phase D (9 Nov 2026): per-cohort LTV re-check.
-- Re-derives sql/09's cohort lifetime value a DIFFERENT way, so a
-- shared bug in one query path cannot survive into the other:
--   * sql/09 used CTEs + substr() on the date_id string + integer
--     month-index subtraction for retention.
--   * This file uses materialised temp tables + strftime() on the
--     dim_date date_id + interval membership (date(x, '+N months'))
--     for retention.
-- Both must land on the same per-cohort numbers (tolerance BRL 0.01).
-- Run: sqlite3 data/processed/f1.db < sql/13_cohort_ltv_recheck.sql
-- Reference output: /tmp/ltv_q1.csv was captured from sql/09 on 9 Nov 2026
-- (kept in the run log, not in the repo); src/check_ltv_recheck.py
-- compares the two paths + a pure-Python recompute from the raw CSVs.

-- Step 1: one row per customer — first purchase date, via dim_date.
DROP TABLE IF EXISTS temp.first_buy_r;
CREATE TEMP TABLE first_buy_r AS
SELECT cu.customer_unique_id,
       MIN(d.date_id) AS first_date
FROM fact_order_items f
JOIN dim_customer cu ON cu.customer_id = f.customer_id
JOIN dim_date d ON d.date_id = f.date_id
GROUP BY cu.customer_unique_id;

-- Step 2: cohort month from the first-purchase date.
DROP TABLE IF EXISTS temp.cohort_r;
CREATE TEMP TABLE cohort_r AS
SELECT customer_unique_id,
       strftime('%Y-%m', first_date) AS cohort_month,
       date(first_date, 'start of month') AS cohort_start
FROM first_buy_r;

-- Step 3: lifetime spend per customer (orders + revenue).
DROP TABLE IF EXISTS temp.spend_r;
CREATE TEMP TABLE spend_r AS
SELECT cu.customer_unique_id,
       COUNT(DISTINCT f.order_id) AS orders,
       SUM(f.price) AS revenue
FROM fact_order_items f
JOIN dim_customer cu ON cu.customer_id = f.customer_id
GROUP BY cu.customer_unique_id;

-- Q1: LTV per cohort, re-derived.
SELECT c.cohort_month,
       COUNT(*) AS customers,
       COUNT(*) - SUM(CASE WHEN s.orders = 1 THEN 1 ELSE 0 END) AS repeat_buyers,
       ROUND(100.0 * (COUNT(*) - SUM(CASE WHEN s.orders = 1 THEN 1 ELSE 0 END))
             / COUNT(*), 2) AS repeat_pct,
       ROUND(AVG(s.orders), 3) AS avg_orders_per_customer,
       ROUND(SUM(s.revenue), 2) AS cohort_revenue_brl,
       ROUND(SUM(s.revenue) / COUNT(*), 2) AS ltv_brl_per_customer
FROM cohort_r c
JOIN spend_r s ON s.customer_unique_id = c.customer_unique_id
GROUP BY c.cohort_month
ORDER BY c.cohort_month;

-- Q2: Nov 2017 vs neighbours — retention by interval membership.
-- Month N after first purchase = an order dated in
-- [cohort_start + N months, cohort_start + (N+1) months).
DROP TABLE IF EXISTS temp.activity_r;
CREATE TEMP TABLE activity_r AS
SELECT cu.customer_unique_id, d.date_id AS active_date
FROM fact_order_items f
JOIN dim_customer cu ON cu.customer_id = f.customer_id
JOIN dim_date d ON d.date_id = f.date_id
GROUP BY cu.customer_unique_id, d.date_id;

SELECT c.cohort_month,
       COUNT(DISTINCT c.customer_unique_id) AS customers,
       ROUND(100.0 * COUNT(DISTINCT CASE
             WHEN a.active_date >= date(c.cohort_start, '+1 month')
              AND a.active_date <  date(c.cohort_start, '+2 months')
             THEN c.customer_unique_id END)
             / COUNT(DISTINCT c.customer_unique_id), 2) AS retained_m1_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE
             WHEN a.active_date >= date(c.cohort_start, '+2 months')
              AND a.active_date <  date(c.cohort_start, '+3 months')
             THEN c.customer_unique_id END)
             / COUNT(DISTINCT c.customer_unique_id), 2) AS retained_m2_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE
             WHEN a.active_date >= date(c.cohort_start, '+3 months')
              AND a.active_date <  date(c.cohort_start, '+4 months')
             THEN c.customer_unique_id END)
             / COUNT(DISTINCT c.customer_unique_id), 2) AS retained_m3_pct
FROM cohort_r c
LEFT JOIN activity_r a ON a.customer_unique_id = c.customer_unique_id
WHERE c.cohort_month IN ('2017-10', '2017-11', '2017-12')
GROUP BY c.cohort_month
ORDER BY c.cohort_month;

-- Q3: the flat-LTV claim, stated as numbers — LTV range among cohorts
-- with more than 300 customers, and the overall weighted average.
SELECT MIN(ltv) AS min_ltv_big_cohorts,
       MAX(ltv) AS max_ltv_big_cohorts,
       ROUND(SUM(revenue) / SUM(customers), 2) AS overall_ltv_brl
FROM (
  SELECT COUNT(*) AS customers,
         SUM(s.revenue) AS revenue,
         SUM(s.revenue) / COUNT(*) AS ltv
  FROM cohort_r c
  JOIN spend_r s ON s.customer_unique_id = c.customer_unique_id
  GROUP BY c.cohort_month
  HAVING COUNT(*) > 300
);
