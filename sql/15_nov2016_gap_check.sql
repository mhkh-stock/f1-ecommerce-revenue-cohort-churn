-- FLAGSHIP 1 — Phase D: November 2016 gap check (11 Nov 2026)
--
-- Question: the cohort analysis found 23 cohorts but none for
-- Nov 2016 (Sep 2016, Oct 2016, then Dec 2016). Is November 2016
-- a hole in our load, or is it genuinely absent from the source?
--
-- Answer (verified by src/check_nov2016_gap.py, two independent
-- paths): the raw Olist orders file itself contains ZERO orders
-- with a purchase timestamp in November 2016. The gap is in the
-- source data, not in the ingest. October 2016 item-bearing
-- purchases span only 2–10 Oct (one cancelled order on 22 Oct, no
-- items), and December 2016 holds exactly one order (23 Dec). The
-- 2016 is a 329-order pilot fragment, 0.37% of the dataset's
-- revenue — the clean monthly series starts Jan 2017.
--
-- Run: sqlite3 data/processed/f1.db < sql/15_nov2016_gap_check.sql
-- (read-only queries; no staging table needed — the raw-CSV side
-- of the comparison lives in src/check_nov2016_gap.py).

-- Q1: monthly orders / items / revenue, Sep 2016 – Jan 2017, star schema.
-- (Item-bearing orders only: fact rows carry the purchase date.)
SELECT 'Q1 monthly' AS check_name,
       substr(d.date_id, 1, 7) AS month,
       COUNT(DISTINCT f.order_id) AS orders,
       COUNT(*) AS items,
       ROUND(SUM(f.price), 2) AS revenue_brl
FROM fact_order_items f
JOIN dim_date d ON d.date_id = f.date_id
WHERE substr(d.date_id, 1, 7) BETWEEN '2016-09' AND '2017-01'
GROUP BY month
ORDER BY month;

-- Q2: dim_date coverage Sep–Dec 2016. dim_date is a presence spine:
-- one row per distinct purchase date in the ORDERS file (all orders,
-- including item-less ones), NOT a full calendar — so a month with
-- no purchases has no rows at all. Fact covers 616 of the 634 dates;
-- the other 18 are dates whose orders all lack items.
SELECT 'Q2 dim_date' AS check_name,
       substr(date_id, 1, 7) AS month,
       COUNT(*) AS dates_present,
       MIN(date_id) AS first_date,
       MAX(date_id) AS last_date
FROM dim_date
WHERE substr(date_id, 1, 7) BETWEEN '2016-09' AND '2016-12'
GROUP BY month
ORDER BY month;

-- Q3: 2016 cohorts — first-purchase month per unique customer.
SELECT 'Q3 cohort' AS check_name,
       substr(firstd, 1, 7) AS cohort_month,
       COUNT(*) AS customers
FROM (
    SELECT c.customer_unique_id, MIN(d.date_id) AS firstd
    FROM fact_order_items f
    JOIN dim_date d ON d.date_id = f.date_id
    JOIN dim_customer c ON c.customer_id = f.customer_id
    GROUP BY c.customer_unique_id
)
WHERE cohort_month LIKE '2016%'
GROUP BY cohort_month
ORDER BY cohort_month;

-- Q4: 2016 totals — the whole pilot fragment in one row.
SELECT 'Q4 2016 total' AS check_name,
       COUNT(DISTINCT f.order_id) AS orders,
       COUNT(*) AS items,
       ROUND(SUM(f.price), 2) AS revenue_brl,
       COUNT(DISTINCT c.customer_unique_id) AS customers
FROM fact_order_items f
JOIN dim_date d ON d.date_id = f.date_id
JOIN dim_customer c ON c.customer_id = f.customer_id
WHERE d.order_year = 2016;

-- Q5: dim_date spine integrity — 634 rows, and the 18 rows with no
-- fact rows are exactly the dates whose orders all lack items.
SELECT 'Q5 spine' AS check_name,
       (SELECT COUNT(*) FROM dim_date) AS dim_date_rows,
       (SELECT COUNT(DISTINCT date_id) FROM fact_order_items) AS fact_dates,
       (SELECT COUNT(*) FROM dim_date d
         WHERE NOT EXISTS (SELECT 1 FROM fact_order_items f
                           WHERE f.date_id = d.date_id)) AS empty_dates;
