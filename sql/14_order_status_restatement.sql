-- FLAGSHIP 1 — Phase D order-status restatement (10 Nov 2026)
-- Restates the headline numbers excluding cancelled + unavailable
-- orders, plus a delivered-only view, so the executive summary can
-- quote revenue that was actually earned. The star schema carries no
-- order status (PLAN.md gap, decided 4 Nov 2026), so status comes
-- from the raw orders file via a staging table loaded once per run.
--
-- Load the staging table first (from the project root, on a COPY of
-- the database, never the live file):
--   cp data/processed/f1.db /tmp/f1_restate.db
--   sqlite3 /tmp/f1_restate.db
--   CREATE TABLE tmp_orders_raw (order_id TEXT, customer_id TEXT, order_status TEXT, order_purchase_timestamp TEXT, order_approved_at TEXT, order_delivered_carrier_date TEXT, order_delivered_customer_date TEXT, order_estimated_delivery_date TEXT)
--   .mode csv
--   .import --skip 1 data/raw/olist_orders_dataset.csv tmp_orders_raw
--   CREATE TABLE stg_order_status AS SELECT order_id, order_status FROM tmp_orders_raw
--   DROP TABLE tmp_orders_raw
-- Then run this file:
--   sqlite3 -header -column /tmp/f1_restate.db < sql/14_order_status_restatement.sql
-- Verified by: python3 src/check_order_status.py (SQL + pure-Python
-- recompute from the raw Olist CSVs, no database)
--
-- Published all-status headlines under test (Phase B/C, validated
-- 8 Nov 2026): 112,650 fact rows, 98,666 orders, revenue
-- BRL 13,591,643.70, freight BRL 2,256,599.44, 95,420 customers,
-- 2,913 repeat buyers, churned 66,802 / active 28,618.

-- Q0 — Staging guard: is the status table loaded and complete, and
-- does every fact row carry a status (no orphaned rows)?
-- Checks: 99,441 status rows, 8 distinct statuses, 0 fact rows
-- without a status.
SELECT 'Q0 staging' AS check_name,
       (SELECT COUNT(*) FROM stg_order_status) AS status_rows,
       (SELECT COUNT(DISTINCT order_status) FROM stg_order_status)
           AS distinct_statuses,
       (SELECT COUNT(*)
        FROM fact_order_items f
        LEFT JOIN stg_order_status s ON s.order_id = f.order_id
        WHERE s.order_id IS NULL) AS fact_rows_no_status;

-- Q1 — Revenue and freight by order status, on fact rows only.
-- Checks: per-status orders sum to 98,666, revenue sums to
-- BRL 13,591,643.70, freight sums to BRL 2,256,599.44.
SELECT 'Q1 by status' AS check_name,
       s.order_status,
       COUNT(DISTINCT f.order_id) AS orders_with_items,
       COUNT(*) AS fact_rows,
       ROUND(SUM(f.price), 2) AS revenue_brl,
       ROUND(SUM(f.freight_value), 2) AS freight_brl
FROM fact_order_items f
JOIN stg_order_status s ON s.order_id = f.order_id
GROUP BY s.order_status
ORDER BY orders_with_items DESC;

-- Q1b — Orders that never reached the fact table, by status.
-- These carried no items and no revenue. Checks: rows sum to 775
-- (99,441 raw orders minus 98,666 orders with items).
SELECT 'Q1b no items' AS check_name,
       s.order_status,
       COUNT(*) AS orders_no_items
FROM stg_order_status s
LEFT JOIN (SELECT DISTINCT order_id FROM fact_order_items) f
    ON f.order_id = s.order_id
WHERE f.order_id IS NULL
GROUP BY s.order_status
ORDER BY orders_no_items DESC;

-- Q2 — Restated headlines: every status EXCEPT cancelled and
-- unavailable. This is the revenue the business actually earned.
-- Checks: Python recompute from the raw CSVs (see check_order_status.py).
WITH restated AS (
    SELECT f.order_id, f.price, f.freight_value, c.customer_unique_id
    FROM fact_order_items f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
)
SELECT 'Q2 restated' AS check_name,
       (SELECT COUNT(DISTINCT order_id) FROM restated) AS orders,
       (SELECT COUNT(*) FROM restated) AS fact_rows,
       ROUND((SELECT SUM(price) FROM restated), 2) AS revenue_brl,
       ROUND((SELECT SUM(freight_value) FROM restated), 2) AS freight_brl,
       (SELECT COUNT(DISTINCT customer_unique_id) FROM restated) AS customers,
       (SELECT COUNT(*)
        FROM (SELECT customer_unique_id FROM restated
              GROUP BY customer_unique_id
              HAVING COUNT(DISTINCT order_id) > 1)) AS repeat_buyers,
       ROUND((SELECT SUM(price) FROM restated)
             / (SELECT COUNT(DISTINCT customer_unique_id) FROM restated), 2)
           AS avg_spend_brl;

-- Q3 — Delivered-only headlines: the strictest revenue definition,
-- only orders that reached the customer. Shown for comparison, not
-- recommended as the headline (it drops in-flight orders that are
-- real revenue in progress).
WITH delivered AS (
    SELECT f.order_id, f.price, f.freight_value, c.customer_unique_id
    FROM fact_order_items f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status = 'delivered'
)
SELECT 'Q3 delivered-only' AS check_name,
       (SELECT COUNT(DISTINCT order_id) FROM delivered) AS orders,
       (SELECT COUNT(*) FROM delivered) AS fact_rows,
       ROUND((SELECT SUM(price) FROM delivered), 2) AS revenue_brl,
       ROUND((SELECT SUM(freight_value) FROM delivered), 2) AS freight_brl,
       (SELECT COUNT(DISTINCT customer_unique_id) FROM delivered) AS customers,
       (SELECT COUNT(*)
        FROM (SELECT customer_unique_id FROM delivered
              GROUP BY customer_unique_id
              HAVING COUNT(DISTINCT order_id) > 1)) AS repeat_buyers,
       ROUND((SELECT SUM(price) FROM delivered)
             / (SELECT COUNT(DISTINCT customer_unique_id) FROM delivered), 2)
           AS avg_spend_brl;

-- Q4 — Delta of each restated definition vs the published all-status
-- headlines, in units and in percent. The published values are
-- literals from the Phase B/C validation (8 Nov 2026).
WITH published AS (
    SELECT 98666 AS orders, 112650 AS fact_rows,
           13591643.70 AS revenue_brl, 2256599.44 AS freight_brl,
           95420 AS customers, 2913 AS repeat_buyers
),
restated AS (
    SELECT COUNT(DISTINCT f.order_id) AS orders, COUNT(*) AS fact_rows,
           ROUND(SUM(f.price), 2) AS revenue_brl,
           ROUND(SUM(f.freight_value), 2) AS freight_brl,
           COUNT(DISTINCT c.customer_unique_id) AS customers,
           (SELECT COUNT(*)
            FROM (SELECT c2.customer_unique_id
                  FROM fact_order_items f2
                  JOIN dim_customer c2 ON c2.customer_id = f2.customer_id
                  JOIN stg_order_status s2 ON s2.order_id = f2.order_id
                  WHERE s2.order_status NOT IN ('canceled', 'unavailable')
                  GROUP BY c2.customer_unique_id
                  HAVING COUNT(DISTINCT f2.order_id) > 1)) AS repeat_buyers
    FROM fact_order_items f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
),
delivered AS (
    SELECT COUNT(DISTINCT f.order_id) AS orders, COUNT(*) AS fact_rows,
           ROUND(SUM(f.price), 2) AS revenue_brl,
           ROUND(SUM(f.freight_value), 2) AS freight_brl,
           COUNT(DISTINCT c.customer_unique_id) AS customers,
           (SELECT COUNT(*)
            FROM (SELECT c2.customer_unique_id
                  FROM fact_order_items f2
                  JOIN dim_customer c2 ON c2.customer_id = f2.customer_id
                  JOIN stg_order_status s2 ON s2.order_id = f2.order_id
                  WHERE s2.order_status = 'delivered'
                  GROUP BY c2.customer_unique_id
                  HAVING COUNT(DISTINCT f2.order_id) > 1)) AS repeat_buyers
    FROM fact_order_items f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status = 'delivered'
)
SELECT 'Q4a delta restated' AS check_name,
       r.orders - p.orders AS orders_delta,
       ROUND(100.0 * (r.orders - p.orders) / p.orders, 2) AS orders_delta_pct,
       ROUND(r.revenue_brl - p.revenue_brl, 2) AS revenue_delta_brl,
       ROUND(100.0 * (r.revenue_brl - p.revenue_brl) / p.revenue_brl, 2)
           AS revenue_delta_pct,
       r.customers - p.customers AS customers_delta,
       r.repeat_buyers - p.repeat_buyers AS repeat_buyers_delta
FROM restated r, published p
UNION ALL
SELECT 'Q4b delta delivered-only' AS check_name,
       d.orders - p.orders,
       ROUND(100.0 * (d.orders - p.orders) / p.orders, 2),
       ROUND(d.revenue_brl - p.revenue_brl, 2),
       ROUND(100.0 * (d.revenue_brl - p.revenue_brl) / p.revenue_brl, 2),
       d.customers - p.customers,
       d.repeat_buyers - p.repeat_buyers
FROM delivered d, published p;

-- Q5 — Churn under the restated definition (same cut-off as Phase C:
-- cut-off 2018-10-17, churned = last purchase before 2018-04-17),
-- written as set difference exactly like sql/12 Q3 so the two runs
-- are comparable. Checks: churn rate barely moves vs 66,802 / 28,618.
WITH purchasers AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
),
active AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN dim_date d ON d.date_id = f.date_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
      AND d.date_id >= '2018-04-17'
),
churned AS (
    SELECT customer_unique_id FROM purchasers
    EXCEPT
    SELECT customer_unique_id FROM active
)
SELECT 'Q5 churn restated' AS check_name,
       (SELECT COUNT(*) FROM churned) AS churned,
       (SELECT COUNT(*) FROM active) AS active;

-- Q6 — Churn under the delivered-only definition, same cut-off.
-- Checks: churn rate barely moves vs 66,802 / 28,618.
WITH purchasers AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status = 'delivered'
),
active AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN dim_date d ON d.date_id = f.date_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status = 'delivered'
      AND d.date_id >= '2018-04-17'
),
churned AS (
    SELECT customer_unique_id FROM purchasers
    EXCEPT
    SELECT customer_unique_id FROM active
)
SELECT 'Q6 churn delivered-only' AS check_name,
       (SELECT COUNT(*) FROM churned) AS churned,
       (SELECT COUNT(*) FROM active) AS active;

-- Q7 — At-risk under the restated definition (same windows as
-- sql/12 Q5: a purchase in 2018-04-17..2018-07-17 and none on/after
-- 2018-07-17), plus the at-risk REPEAT buyers behind the
-- recommendations.md figure (617 customers, BRL 169,495.02).
-- Checks: Python recompute from the raw CSVs.
WITH in_window AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN dim_date d ON d.date_id = f.date_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
      AND d.date_id >= '2018-04-17' AND d.date_id < '2018-07-17'
),
after_window AS (
    SELECT DISTINCT c.customer_unique_id
    FROM dim_customer c
    JOIN fact_order_items f ON f.customer_id = c.customer_id
    JOIN dim_date d ON d.date_id = f.date_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
      AND d.date_id >= '2018-07-17'
),
at_risk AS (
    SELECT customer_unique_id FROM in_window
    EXCEPT
    SELECT customer_unique_id FROM after_window
),
at_risk_repeat AS (
    SELECT c.customer_unique_id
    FROM fact_order_items f
    JOIN dim_customer c ON c.customer_id = f.customer_id
    JOIN stg_order_status s ON s.order_id = f.order_id
    WHERE s.order_status NOT IN ('canceled', 'unavailable')
      AND c.customer_unique_id IN (SELECT customer_unique_id FROM at_risk)
    GROUP BY c.customer_unique_id
    HAVING COUNT(DISTINCT f.order_id) > 1
)
SELECT 'Q7 at-risk restated' AS check_name,
       (SELECT COUNT(*) FROM at_risk) AS at_risk_customers,
       ROUND((SELECT SUM(f.price)
              FROM fact_order_items f
              JOIN dim_customer c ON c.customer_id = f.customer_id
              JOIN stg_order_status s ON s.order_id = f.order_id
              WHERE s.order_status NOT IN ('canceled', 'unavailable')
                AND c.customer_unique_id IN (SELECT customer_unique_id FROM at_risk)
             ), 2) AS at_risk_revenue_brl,
       (SELECT COUNT(*) FROM at_risk_repeat) AS at_risk_repeat_buyers,
       ROUND((SELECT SUM(f.price)
              FROM fact_order_items f
              JOIN dim_customer c ON c.customer_id = f.customer_id
              JOIN stg_order_status s ON s.order_id = f.order_id
              WHERE s.order_status NOT IN ('canceled', 'unavailable')
                AND c.customer_unique_id IN (SELECT customer_unique_id FROM at_risk_repeat)
             ), 2) AS at_risk_repeat_revenue_brl;
