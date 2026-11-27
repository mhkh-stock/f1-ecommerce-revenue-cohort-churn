-- Flagship 1, Phase B (step 1, 3 Nov 2026): cohort sizes from the REAL star schema.
-- Cohort = first purchase month of a customer_unique_id (NOT customer_id:
-- customer_id is near-unique per order, so counting it would show zero repeats).
-- Run: sqlite3 data/processed/f1.db < sql/01_cohort_sizes.sql
WITH first_buy AS (
  SELECT cu.customer_unique_id, MIN(f.date_id) AS first_date
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
)
SELECT substr(first_date, 1, 7) AS cohort_month, COUNT(*) AS new_customers
FROM first_buy GROUP BY cohort_month ORDER BY cohort_month;
