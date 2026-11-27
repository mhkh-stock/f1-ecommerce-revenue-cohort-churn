-- 05 — Revenue by customer state (Phase A, revenue leak pack)
-- Business question: how concentrated is revenue geographically?
-- Customers are counted by customer_unique_id (see PLAN.md: raw
-- customer_id is near-unique per order and must never count people).
-- Verified on data/processed/f1.db (112,650 fact rows).

SELECT
    c.customer_state AS state,
    COUNT(DISTINCT c.customer_unique_id) AS customers,
    COUNT(DISTINCT f.order_id) AS orders,
    COUNT(*) AS items,
    ROUND(SUM(f.price), 2) AS revenue_brl,
    ROUND(100.0 * SUM(f.price) / SUM(SUM(f.price)) OVER (), 2) AS revenue_share_pct,
    ROUND(SUM(f.price) / COUNT(DISTINCT c.customer_unique_id), 2) AS revenue_per_customer_brl
FROM fact_order_items f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.customer_state
ORDER BY revenue_brl DESC;
