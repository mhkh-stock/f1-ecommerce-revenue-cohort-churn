-- FLAGSHIP 1 — Phase D clean 2017–2018 trend (12 Nov 2026)
-- The monthly trend the executive summary charts. The 11 Nov gap
-- check locked the decision: trend charts start Jan 2017, because
-- 2016 is a 329-order pilot fragment (BRL 49,785.92, 0.37% of
-- revenue) with a zero-order November that would read as a collapse
-- that never happened. This file builds the clean series.
--
-- Revenue here is the RESTATED figure (10 Nov 2026): cancelled +
-- unavailable orders excluded. The star schema carries no order
-- status (PLAN.md gap), so status comes from the raw orders file
-- via a staging table — load it first, on a COPY of the database
-- (never the live file), exactly as sql/14 does:
--   cp data/processed/f1.db /tmp/f1_trend.db
--   sqlite3 /tmp/f1_trend.db
--   CREATE TABLE tmp_orders_raw (order_id TEXT, customer_id TEXT, order_status TEXT, order_purchase_timestamp TEXT, order_approved_at TEXT, order_delivered_carrier_date TEXT, order_delivered_customer_date TEXT, order_estimated_delivery_date TEXT)
--   .mode csv
--   .import --skip 1 data/raw/olist_orders_dataset.csv tmp_orders_raw
--   CREATE TABLE stg_order_status AS SELECT order_id, order_status FROM tmp_orders_raw
--   DROP TABLE tmp_orders_raw
-- Then run this file:
--   sqlite3 -header -column /tmp/f1_trend.db < sql/16_clean_trend_2017_2018.sql
-- Verified by: python3 src/check_clean_trend.py (SQL + pure-Python
-- recompute from the raw Olist CSVs, no database)
--
-- Published restated headline under test (10 Nov 2026): revenue
-- excl. cancelled + unavailable BRL 13,494,400.74, 98,199 orders,
-- 94,983 customers.

-- Q0 — Staging guard: is the status table loaded and complete?
SELECT 'Q0 staging' AS check_name,
       (SELECT COUNT(*) FROM stg_order_status) AS status_rows,
       (SELECT COUNT(DISTINCT order_status) FROM stg_order_status)
           AS distinct_statuses,
       (SELECT COUNT(*)
        FROM fact_order_items f
        LEFT JOIN stg_order_status s ON s.order_id = f.order_id
        WHERE s.order_id IS NULL) AS fact_rows_no_status;

-- Q1 — Clean monthly trend, Jan 2017 → Aug 2018 (20 months).
-- Grain: one row per calendar month. Restated revenue (cancelled +
-- unavailable excluded), orders = distinct orders with items,
-- AOV = revenue / orders. MoM and YoY growth via LAG() so a single
-- strong month is never mistaken for a trend.
--
-- The series STOPS at Aug 2018 on purpose. September 2018 holds
-- 16 raw orders, 15 of them cancelled and 1 shipped — a BRL 145.00
-- month that would read as a 99.98% collapse that never happened.
-- The Olist extract simply ends at the end of Aug 2018 (Oct 2018
-- holds 4 cancelled orders and nothing else). Sep–Oct 2018 belong
-- in the Q2 stub, labelled, never on the trend line — the same
-- rule the 11 Nov gap check set for 2016.
SELECT
    d.order_year  AS year,
    d.order_month AS month,
    COUNT(DISTINCT f.order_id) AS orders,
    COUNT(*) AS items,
    ROUND(SUM(f.price), 2) AS revenue_brl,
    ROUND(SUM(f.freight_value), 2) AS freight_brl,
    ROUND(SUM(f.price) / COUNT(DISTINCT f.order_id), 2) AS aov_brl,
    ROUND(
        100.0 * (SUM(f.price) - LAG(SUM(f.price)) OVER
                 (ORDER BY d.order_year, d.order_month))
        / LAG(SUM(f.price)) OVER
          (ORDER BY d.order_year, d.order_month),
        2
    ) AS mom_growth_pct,
    ROUND(
        100.0 * (SUM(f.price) - LAG(SUM(f.price), 12) OVER
                 (ORDER BY d.order_year, d.order_month))
        / LAG(SUM(f.price), 12) OVER
          (ORDER BY d.order_year, d.order_month),
        2
    ) AS yoy_growth_pct,
    ROUND(SUM(SUM(f.price)) OVER
          (ORDER BY d.order_year, d.order_month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2)
        AS cumulative_revenue_brl
FROM fact_order_items f
JOIN dim_date d ON d.date_id = f.date_id
JOIN stg_order_status s ON s.order_id = f.order_id
WHERE s.order_status NOT IN ('canceled', 'unavailable')
  AND (d.order_year, d.order_month) >= (2017, 1)
  AND (d.order_year, d.order_month) <= (2018, 8)
GROUP BY d.order_year, d.order_month
ORDER BY d.order_year, d.order_month;

-- Q2 — The stubs, for the labelled fragments in the chart (never
-- part of the trend line). 2016: Sep, Oct, Dec (November 2016
-- returns NO row — the gap check proved the raw file holds zero
-- November 2016 orders; the stub must say so, not invent a zero).
-- 2018 tail: Sep 2018 only (1 shipped order, BRL 145.00; Oct 2018
-- returns no row — its 4 orders are all cancelled, none with items).
-- Same restated definition throughout.
SELECT
    d.order_year  AS year,
    d.order_month AS month,
    COUNT(DISTINCT f.order_id) AS orders,
    COUNT(*) AS items,
    ROUND(SUM(f.price), 2) AS revenue_brl
FROM fact_order_items f
JOIN dim_date d ON d.date_id = f.date_id
JOIN stg_order_status s ON s.order_id = f.order_id
WHERE s.order_status NOT IN ('canceled', 'unavailable')
  AND ((d.order_year = 2016)
       OR (d.order_year = 2018 AND d.order_month = 9))
GROUP BY d.order_year, d.order_month
ORDER BY d.order_year, d.order_month;

-- Q3 — Summary facts for the executive summary: peak and trough
-- months, 2017 vs 2018 (Jan–Aug) totals, H1 2018 vs H1 2017.
-- (Peak/trough/month totals are read off Q1 in the check script;
-- this query pins the half-year comparison in SQL.)
SELECT 'Q3 half years' AS check_name,
       ROUND(SUM(CASE WHEN d.order_year = 2017
                       AND d.order_month BETWEEN 1 AND 6
                  THEN f.price ELSE 0 END), 2) AS h1_2017_brl,
       ROUND(SUM(CASE WHEN d.order_year = 2018
                       AND d.order_month BETWEEN 1 AND 6
                  THEN f.price ELSE 0 END), 2) AS h1_2018_brl,
       ROUND(100.0 * (SUM(CASE WHEN d.order_year = 2018
                                AND d.order_month BETWEEN 1 AND 6
                           THEN f.price ELSE 0 END)
                      - SUM(CASE WHEN d.order_year = 2017
                                 AND d.order_month BETWEEN 1 AND 6
                            THEN f.price ELSE 0 END))
             / SUM(CASE WHEN d.order_year = 2017
                        AND d.order_month BETWEEN 1 AND 6
                   THEN f.price ELSE 0 END), 2) AS h1_growth_pct,
       ROUND(SUM(CASE WHEN d.order_year = 2017
                  THEN f.price ELSE 0 END), 2) AS total_2017_brl,
       ROUND(SUM(CASE WHEN d.order_year = 2018
                  THEN f.price ELSE 0 END), 2) AS total_2018_jan_aug_brl
FROM fact_order_items f
JOIN dim_date d ON d.date_id = f.date_id
JOIN stg_order_status s ON s.order_id = f.order_id
WHERE s.order_status NOT IN ('canceled', 'unavailable')
  AND (d.order_year, d.order_month) >= (2017, 1)
  AND (d.order_year, d.order_month) <= (2018, 8);
