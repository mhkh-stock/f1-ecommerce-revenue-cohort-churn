-- Flagship 1, Phase C (step 1, 7 Nov 2026): RFM segments.
-- Revenue = SUM(price) only. Freight is delivery cost, never revenue
-- (see revenue_leak_notes.md). Customers are counted by
-- customer_unique_id (customer_id is near-unique per order).
-- Cut-off ("today") is 2018-10-17, the dataset end per
-- cohort_definitions.md. Note: the last item-bearing purchase is
-- 2018-09-03; the 16 orders after that date are all cancelled with no
-- items, so the 44 days to 2018-10-17 are dead time and every recency
-- carries a +44-day floor. See analysis/rfm_churn.md for the effect.
-- Run: sqlite3 data/processed/f1.db < sql/10_rfm_segments.sql

-- Q1: RFM base totals — reconciliation anchor. 95,420 customers with
-- at least one fact row (676 of the 96,096 unique ids in dim_customer
-- have no fact row and belong to no segment), 98,666 orders,
-- BRL 13,591,643.70 of revenue.
WITH rfm AS (
  SELECT cu.customer_unique_id,
         CAST(julianday('2018-10-17') - julianday(MAX(f.date_id))
              AS INTEGER) AS recency_days,
         COUNT(DISTINCT f.order_id) AS frequency,
         SUM(f.price) AS monetary
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
)
SELECT COUNT(*) AS customers,
       SUM(frequency) AS orders,
       ROUND(SUM(monetary), 2) AS revenue_brl,
       MIN(recency_days) AS min_recency_days,
       MAX(recency_days) AS max_recency_days,
       MIN(frequency) AS min_frequency,
       MAX(frequency) AS max_frequency
FROM rfm;

-- Q2: quintile boundaries for each score. Scores are NTILE(5): R is
-- reversed so 5 is most recent, F and M rise with value. Read the
-- ranges, not just the score: F buckets 1-4 hold only frequency-1
-- customers (see Q4), and shared edge values (e.g. recency 433 in
-- both R1 and R2) are same-day ties split across adjacent quintiles
-- by NTILE, not real differences.
WITH rfm AS (
  SELECT cu.customer_unique_id,
         CAST(julianday('2018-10-17') - julianday(MAX(f.date_id))
              AS INTEGER) AS recency_days,
         COUNT(DISTINCT f.order_id) AS frequency,
         SUM(f.price) AS monetary
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
scored AS (
  SELECT *,
         6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
         NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
         NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
  FROM rfm
)
SELECT 'R (days since last purchase)' AS score_type, r_score AS score,
       COUNT(*) AS customers, MIN(recency_days) AS value_min,
       MAX(recency_days) AS value_max
FROM scored GROUP BY r_score
UNION ALL
SELECT 'F (orders)', f_score, COUNT(*), MIN(frequency), MAX(frequency)
FROM scored GROUP BY f_score
UNION ALL
SELECT 'M (BRL spent)', m_score, COUNT(*),
       ROUND(MIN(monetary), 2), ROUND(MAX(monetary), 2)
FROM scored GROUP BY m_score
ORDER BY score_type, score;

-- Q3: named segments. Segments are built from R score plus the ACTUAL
-- order count, not from F score: 96.9% of customers have frequency 1,
-- so NTILE splits identical frequency-1 values across F buckets 1-5
-- arbitrarily (Q4 proves it), and a segment map built on F score
-- would label ~16,000 one-time buyers "Champions". The map below is
-- exhaustive and mutually exclusive: every (R score, order count)
-- pair lands in exactly one segment.
WITH rfm AS (
  SELECT cu.customer_unique_id,
         CAST(julianday('2018-10-17') - julianday(MAX(f.date_id))
              AS INTEGER) AS recency_days,
         COUNT(DISTINCT f.order_id) AS frequency,
         SUM(f.price) AS monetary
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
scored AS (
  SELECT *,
         6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
         NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
         NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
  FROM rfm
),
segmented AS (
  SELECT *,
    CASE
      WHEN r_score >= 4 AND frequency >= 3 THEN 'Champions'
      WHEN r_score IN (4, 5) AND frequency = 2 THEN 'Loyal'
      WHEN r_score = 3 AND frequency >= 2 THEN 'Potential Loyalists'
      WHEN r_score IN (4, 5) AND frequency = 1 THEN 'Recent One-Time'
      WHEN r_score = 3 AND frequency = 1 THEN 'Fading One-Time'
      WHEN r_score = 2 AND frequency >= 2 THEN 'At-Risk'
      WHEN r_score = 2 AND frequency = 1 THEN 'At-Risk One-Time'
      WHEN r_score = 1 AND frequency >= 2 THEN 'Hibernating'
      ELSE 'Lost'
    END AS segment
  FROM scored
)
SELECT segment,
       COUNT(*) AS customers,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM segmented), 2)
           AS customer_share_pct,
       ROUND(SUM(monetary), 2) AS revenue_brl,
       ROUND(100.0 * SUM(monetary)
             / (SELECT SUM(monetary) FROM segmented), 2)
           AS revenue_share_pct,
       ROUND(AVG(monetary), 2) AS avg_monetary_brl,
       ROUND(AVG(recency_days), 1) AS avg_recency_days
FROM segmented
GROUP BY segment
ORDER BY customers DESC;

-- Q4: F-score diagnostic — why segments do not use F score. NTILE(5)
-- over frequency forces ~19,084 customers into each bucket even
-- though 92,507 customers share the identical value frequency = 1.
-- Buckets 1-4 are 100% one-time buyers and bucket 5 mixes 16,171
-- one-time buyers with all 2,913 repeat buyers. F score therefore
-- carries no information about repeat behaviour in this dataset.
WITH rfm AS (
  SELECT cu.customer_unique_id,
         CAST(julianday('2018-10-17') - julianday(MAX(f.date_id))
              AS INTEGER) AS recency_days,
         COUNT(DISTINCT f.order_id) AS frequency,
         SUM(f.price) AS monetary
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
scored AS (
  SELECT *,
         NTILE(5) OVER (ORDER BY frequency ASC) AS f_score
  FROM rfm
)
SELECT f_score,
       COUNT(*) AS customers,
       SUM(CASE WHEN frequency = 1 THEN 1 ELSE 0 END)
           AS one_time_buyers_in_bucket,
       SUM(CASE WHEN frequency >= 2 THEN 1 ELSE 0 END)
           AS repeat_buyers_in_bucket
FROM scored
GROUP BY f_score
ORDER BY f_score;
