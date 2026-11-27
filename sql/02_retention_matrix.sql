-- Flagship 1, Phase B (step 2, definition + draft): retention matrix shape.
-- Cell (cohort, m) = share of that cohort's customers with at least one order
-- in month m after their first purchase month. Month 0 is 100% by construction.
-- NOTE: cohorts from Jun 2018 onward are right-censored by the dataset ending
-- 2018-10-17 (their later months simply do not exist yet) — read those rows
-- as incomplete, not as churn. Verified to execute on f1.db; full matrix
-- values are built in the Phase B run (5–6 Nov), not pasted from a draft.
WITH first_buy AS (
  SELECT cu.customer_unique_id, MIN(f.date_id) AS first_date
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id
),
activity AS (
  SELECT cu.customer_unique_id, substr(f.date_id, 1, 7) AS active_month
  FROM fact_order_items f
  JOIN dim_customer cu ON cu.customer_id = f.customer_id
  GROUP BY cu.customer_unique_id, active_month
)
SELECT fb.cohort_month, a.active_month, COUNT(DISTINCT a.customer_unique_id) AS active_customers
FROM (SELECT customer_unique_id, substr(first_date, 1, 7) AS cohort_month FROM first_buy) fb
JOIN activity a ON a.customer_unique_id = fb.customer_unique_id
GROUP BY fb.cohort_month, a.active_month
ORDER BY fb.cohort_month, a.active_month;
