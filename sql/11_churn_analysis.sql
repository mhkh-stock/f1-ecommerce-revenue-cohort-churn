-- Flagship 1, Phase C (step 2, 7 Nov 2026): churn analysis.
-- Revenue = SUM(price) only. Customers are counted by
-- customer_unique_id. Cut-off ("today") is 2018-10-17, the dataset
-- end per cohort_definitions.md. Churn = no purchase in the 6 months
-- before the cut-off, i.e. last purchase before 2018-04-17. At-risk =
-- last purchase 3-6 months before the cut-off (2018-04-17 to
-- 2018-07-17). Cut-off sensitivity is measured in Q6: the last
-- item-bearing purchase is 2018-09-03 (the 16 later orders are all
-- cancelled with no items), so the 2018-10-17 cut-off overstates
-- churn versus a 2018-09-03 cut-off — reported, not hidden.
-- Run: sqlite3 data/processed/f1.db < sql/11_churn_analysis.sql

-- Q1: churned vs active — counts, revenue, shares. The two rows sum
-- to 95,420 customers and BRL 13,591,643.70.
WITH cust AS (
  SELECT cu.customer_unique_id,
         MIN(f.date_id) AS first_date,
         MAX(f.date_id) AS last_date,
         COUNT(DISTINCT f.order_id) AS orders,
         SUM(f.price) AS revenue
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
flagged AS (
  SELECT *,
    CASE WHEN last_date < date('2018-10-17', '-6 months')
         THEN 'churned' ELSE 'active' END AS status
  FROM cust
)
SELECT status,
       COUNT(*) AS customers,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flagged), 2)
           AS customer_share_pct,
       ROUND(SUM(revenue), 2) AS revenue_brl,
       ROUND(100.0 * SUM(revenue)
             / (SELECT SUM(revenue) FROM flagged), 2)
           AS revenue_share_pct,
       ROUND(AVG(revenue), 2) AS avg_revenue_per_customer_brl
FROM flagged
GROUP BY status
ORDER BY status;

-- Q2: churn rate by first-purchase cohort year. Read 2018 with the
-- censoring warning: most 2018 first-buyers bought within 6 months
-- of the cut-off, so they count as "active" by construction, not
-- because they retained. The honest comparison is 2016 vs 2017.
WITH cust AS (
  SELECT cu.customer_unique_id,
         MIN(f.date_id) AS first_date,
         MAX(f.date_id) AS last_date,
         COUNT(DISTINCT f.order_id) AS orders,
         SUM(f.price) AS revenue
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
flagged AS (
  SELECT *,
    CASE WHEN last_date < date('2018-10-17', '-6 months')
         THEN 'churned' ELSE 'active' END AS status
  FROM cust
)
SELECT substr(first_date, 1, 4) AS cohort_year,
       COUNT(*) AS customers,
       SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END)
           AS churned_customers,
       ROUND(100.0 * SUM(CASE WHEN status = 'churned' THEN 1 ELSE 0 END)
             / COUNT(*), 2) AS churn_rate_pct,
       ROUND(SUM(CASE WHEN status = 'churned' THEN revenue ELSE 0 END), 2)
           AS churned_revenue_brl
FROM flagged
GROUP BY cohort_year
ORDER BY cohort_year;

-- Q3: at-risk summary — customers whose last purchase was 3-6 months
-- before the cut-off, and the revenue attached to them. At-risk is a
-- subset of active by construction.
WITH cust AS (
  SELECT cu.customer_unique_id,
         MIN(f.date_id) AS first_date,
         MAX(f.date_id) AS last_date,
         COUNT(DISTINCT f.order_id) AS orders,
         SUM(f.price) AS revenue
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
flagged AS (
  SELECT *,
    CASE WHEN last_date >= date('2018-10-17', '-6 months')
              AND last_date < date('2018-10-17', '-3 months')
         THEN 1 ELSE 0 END AS at_risk
  FROM cust
)
SELECT COUNT(*) AS at_risk_customers,
       ROUND(SUM(revenue), 2) AS revenue_at_stake_brl,
       ROUND(AVG(revenue), 2) AS avg_revenue_at_stake_brl,
       SUM(orders) AS orders_at_stake,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM flagged), 2)
           AS share_of_all_customers_pct
FROM flagged
WHERE at_risk = 1;

-- Q4: at-risk split — one-time vs repeat buyers. Only the repeat
-- buyers are plausibly saveable: a one-time buyer whose single
-- purchase was 3-6 months ago has the same ~0.5% return rate as any
-- other one-time buyer, so most of the Q3 "revenue at stake" is
-- phantom. The saveable figure is the repeat-buyer row.
WITH cust AS (
  SELECT cu.customer_unique_id,
         MIN(f.date_id) AS first_date,
         MAX(f.date_id) AS last_date,
         COUNT(DISTINCT f.order_id) AS orders,
         SUM(f.price) AS revenue
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
flagged AS (
  SELECT *,
    CASE WHEN last_date >= date('2018-10-17', '-6 months')
              AND last_date < date('2018-10-17', '-3 months')
         THEN 1 ELSE 0 END AS at_risk
  FROM cust
)
SELECT CASE WHEN orders >= 2 THEN 'repeat buyers (saveable)'
            ELSE 'one-time buyers (phantom at stake)' END AS group_label,
       COUNT(*) AS at_risk_customers,
       ROUND(SUM(revenue), 2) AS revenue_at_stake_brl
FROM flagged
WHERE at_risk = 1
GROUP BY group_label
ORDER BY group_label;

-- Q5: the at-risk list — the 25 highest-value at-risk customers by
-- lifetime spend. customer_unique_id is a pseudonymous key, not
-- personal data. The full list is every customer with last purchase
-- in 2018-04-17 to 2018-07-17 (18,594 customers, see Q3).
WITH cust AS (
  SELECT cu.customer_unique_id,
         MIN(f.date_id) AS first_date,
         MAX(f.date_id) AS last_date,
         COUNT(DISTINCT f.order_id) AS orders,
         SUM(f.price) AS revenue
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
)
SELECT customer_unique_id,
       first_date,
       last_date,
       orders,
       ROUND(revenue, 2) AS revenue_brl
FROM cust
WHERE last_date >= date('2018-10-17', '-6 months')
  AND last_date < date('2018-10-17', '-3 months')
ORDER BY revenue DESC
LIMIT 25;

-- Q6: cut-off sensitivity. Customers whose last purchase falls in
-- 2018-03-03 to 2018-04-17 would flip from churned to active if the
-- cut-off were 2018-09-03 (the last item-bearing purchase) instead
-- of 2018-10-17 (the last order timestamp, 44 dead days later).
-- Honest churn range: 59.50% (2018-09-03 cut-off) to 70.01%
-- (2018-10-17 cut-off). Headline stays 70.01% per the locked
-- definition; the range is the caveat.
WITH cust AS (
  SELECT cu.customer_unique_id,
         MIN(f.date_id) AS first_date,
         MAX(f.date_id) AS last_date,
         COUNT(DISTINCT f.order_id) AS orders,
         SUM(f.price) AS revenue
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
)
SELECT COUNT(CASE WHEN last_date >= '2018-03-03'
                       AND last_date < '2018-04-17'
                  THEN 1 END) AS would_flip_customers,
       COUNT(CASE WHEN last_date < '2018-03-03' THEN 1 END)
           AS churned_under_2018_09_03_cutoff,
       ROUND(100.0 * COUNT(CASE WHEN last_date < '2018-03-03' THEN 1 END)
             / COUNT(*), 2) AS churn_rate_under_2018_09_03_cutoff_pct
FROM cust;
