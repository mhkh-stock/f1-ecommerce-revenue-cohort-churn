-- Flagship 1, Phase B (step 3, 6 Nov 2026): cohort lifetime value.
-- Revenue = SUM(price) only. Freight is delivery cost, never revenue
-- (see revenue_leak_notes.md). Customers are counted by
-- customer_unique_id (customer_id is near-unique per order).
-- Run: sqlite3 data/processed/f1.db < sql/09_cohort_lifetime_value.sql

-- Q1: lifetime value per cohort — total revenue, revenue per customer,
-- orders per customer, repeat-buyer share. Small early cohorts (Sep–Dec
-- 2016) are real but tiny; read their per-customer figures with care.
WITH first_buy AS (
  SELECT cu.customer_unique_id, MIN(f.date_id) AS first_date
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
cohort AS (
  SELECT customer_unique_id, substr(first_date, 1, 7) AS cohort_month
  FROM first_buy
),
spend AS (
  SELECT cu.customer_unique_id,
         COUNT(DISTINCT f.order_id) AS orders,
         SUM(f.price) AS revenue
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
)
SELECT c.cohort_month,
       COUNT(*) AS customers,
       COUNT(*) - SUM(CASE WHEN s.orders = 1 THEN 1 ELSE 0 END)
           AS repeat_buyers,
       ROUND(100.0 * (COUNT(*) - SUM(CASE WHEN s.orders = 1 THEN 1 ELSE 0 END))
           / COUNT(*), 2) AS repeat_pct,
       ROUND(AVG(s.orders), 3) AS avg_orders_per_customer,
       ROUND(SUM(s.revenue), 2) AS cohort_revenue_brl,
       ROUND(SUM(s.revenue) / COUNT(*), 2) AS ltv_brl_per_customer
FROM cohort c
JOIN spend s ON s.customer_unique_id = c.customer_unique_id
GROUP BY c.cohort_month
ORDER BY c.cohort_month;

-- Q2: Nov 2017 (Black Friday, the largest cohort) vs its neighbours —
-- share of each cohort active in months 1, 2 and 3 after first purchase.
-- A discount-acquired cohort is expected to retain worse; this tests it.
WITH first_buy AS (
  SELECT cu.customer_unique_id, MIN(f.date_id) AS first_date
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
cohort AS (
  SELECT customer_unique_id, substr(first_date, 1, 7) AS cohort_month
  FROM first_buy
),
activity AS (
  SELECT cu.customer_unique_id, substr(f.date_id, 1, 7) AS active_month
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id, active_month
),
month_index AS (
  SELECT c.customer_unique_id, c.cohort_month,
         (CAST(substr(a.active_month, 1, 4) AS INTEGER) * 12
          + CAST(substr(a.active_month, 6, 2) AS INTEGER))
         - (CAST(substr(c.cohort_month, 1, 4) AS INTEGER) * 12
          + CAST(substr(c.cohort_month, 6, 2) AS INTEGER)) AS m
  FROM cohort c JOIN activity a
    ON a.customer_unique_id = c.customer_unique_id
)
SELECT cohort_month,
       COUNT(DISTINCT customer_unique_id) AS customers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN m = 1 THEN customer_unique_id END)
             / COUNT(DISTINCT customer_unique_id), 2) AS retained_m1_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN m = 2 THEN customer_unique_id END)
             / COUNT(DISTINCT customer_unique_id), 2) AS retained_m2_pct,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN m = 3 THEN customer_unique_id END)
             / COUNT(DISTINCT customer_unique_id), 2) AS retained_m3_pct
FROM month_index
WHERE cohort_month IN ('2017-10', '2017-11', '2017-12')
GROUP BY cohort_month
ORDER BY cohort_month;
