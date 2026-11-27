-- FLAGSHIP 1 — Phase D validation (8 Nov 2026)
-- Independent re-derivations of the headline numbers. Each query is
-- deliberately written DIFFERENTLY from the Phase B/C queries it
-- checks (set difference instead of CASE on MAX(date), HAVING instead
-- of window counts), so agreement is evidence, not repetition.
-- Run: sqlite3 -header -column data/processed/f1.db < sql/12_validation_reconciliation.sql
-- Verified by: python3 src/validate_headlines.py

-- Q1 — Revenue and freight, straight from the fact table.
-- Checks: Phase B/C headline BRL 13,591,643.70 revenue / BRL 2,256,599.44 freight.
SELECT 'Q1 revenue' AS check_name,
       COUNT(*) AS fact_rows,
       COUNT(DISTINCT order_id) AS orders_with_items,
       ROUND(SUM(price), 2) AS revenue_brl,
       ROUND(SUM(freight_value), 2) AS freight_brl
FROM fact_order_items;

-- Q2 — Customers with at least one purchase, via customer_unique_id.
-- Checks: Phase B/C headline 95,420 customers.
SELECT 'Q2 customers' AS check_name,
       COUNT(DISTINCT c.customer_unique_id) AS customers_with_purchase
FROM fact_order_items f
JOIN dim_customer c ON c.customer_id = f.customer_id;

-- Q3 — Churn via set difference (customers with a purchase on/after
-- 2018-04-17, subtracted from all purchasing customers) — the same
-- logic as NOT EXISTS, written as two single-pass scans so it runs
-- in seconds instead of a correlated scan per customer.
-- Checks: Phase C churned 66,802 / active 28,618 (cut-off 2018-10-17).
WITH purchasers AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
),
active AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN dim_date d ON d.date_id = f.date_id
    WHERE d.date_id >= '2018-04-17'
),
churned AS (
    SELECT customer_unique_id FROM purchasers
    EXCEPT
    SELECT customer_unique_id FROM active
)
SELECT 'Q3 churn' AS check_name,
       (SELECT COUNT(*) FROM churned) AS churned,
       (SELECT COUNT(*) FROM active) AS active;

-- Q4 — Repeat buyers via HAVING (distinct orders > 1 per unique customer).
-- Checks: Phase B/C headline 2,913 repeat buyers.
SELECT 'Q4 repeat buyers' AS check_name,
       COUNT(*) AS repeat_buyers
FROM (
    SELECT c.customer_unique_id
    FROM fact_order_items f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    GROUP BY c.customer_unique_id
    HAVING COUNT(DISTINCT f.order_id) > 1
);

-- Q5 — At-risk via set difference (a purchase in 2018-04-17..2018-07-17
-- and none on/after 2018-07-17), instead of Phase C's BETWEEN on
-- MAX(date). Two single-pass scans.
-- Checks: Phase C at-risk 18,594 customers, BRL 2,751,210.98 at stake.
WITH in_window AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN dim_date d ON d.date_id = f.date_id
    WHERE d.date_id >= '2018-04-17' AND d.date_id < '2018-07-17'
),
after_window AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN dim_date d ON d.date_id = f.date_id
    WHERE d.date_id >= '2018-07-17'
),
at_risk AS (
    SELECT customer_unique_id FROM in_window
    EXCEPT
    SELECT customer_unique_id FROM after_window
)
SELECT 'Q5 at-risk' AS check_name,
       (SELECT COUNT(*) FROM at_risk) AS at_risk_customers,
       ROUND((SELECT SUM(f.price)
              FROM fact_order_items f
              JOIN dim_customer c ON c.customer_id = f.customer_id
              WHERE c.customer_unique_id IN (SELECT customer_unique_id FROM at_risk)
             ), 2) AS at_risk_revenue_brl;

-- Q6 — Overall average spend per customer (the LTV anchor).
-- Checks: Phase B/C BRL 142.44.
SELECT 'Q6 avg spend' AS check_name,
       ROUND(SUM(price) / COUNT(DISTINCT c.customer_unique_id), 2)
           AS avg_spend_per_customer_brl
FROM fact_order_items f
JOIN dim_customer c ON c.customer_id = f.customer_id;
