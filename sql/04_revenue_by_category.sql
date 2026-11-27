-- 04 — Revenue by product category (Phase A, revenue leak pack)
-- Business question: which categories actually carry revenue, and
-- which are long-tail noise?
-- Share uses a window SUM so shares reconcile to 100%.
-- Verified on data/processed/f1.db (112,650 fact rows).

SELECT
    COALESCE(p.product_category_name, '(no category)') AS category,
    COUNT(*) AS items,
    COUNT(DISTINCT f.order_id) AS orders,
    ROUND(SUM(f.price), 2) AS revenue_brl,
    ROUND(100.0 * SUM(f.price) / SUM(SUM(f.price)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(f.price), 2) AS avg_item_price_brl,
    RANK() OVER (ORDER BY SUM(f.price) DESC) AS revenue_rank
FROM fact_order_items f
LEFT JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_category_name
ORDER BY revenue_brl DESC;
