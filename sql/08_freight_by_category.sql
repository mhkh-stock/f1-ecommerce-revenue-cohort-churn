-- 08 — Freight burden by category (Phase A, revenue leak pack)
-- Business question: is the freight leak general, or is it a
-- logistics story for a few categories? This is the cross-tab the
-- revenue leak notes flagged for Phase D — answered here in Phase A
-- so the leak story can name its categories.
-- Grain: one row per product category (NULL category kept as its own
-- row, never silently dropped).
-- Freight is a cost, not revenue. "Over-100%" items cost more to
-- deliver than they sell for, before any other cost.
-- Verified on data/processed/f1.db (112,650 fact rows).

SELECT
    COALESCE(NULLIF(p.product_category_name, ''), '(no category)') AS category,
    COUNT(*) AS items,
    ROUND(SUM(f.price), 2) AS revenue_brl,
    ROUND(SUM(f.freight_value), 2) AS freight_brl,
    ROUND(100.0 * SUM(f.freight_value) / NULLIF(SUM(f.price), 0), 2)
        AS freight_as_pct_of_price,
    SUM(CASE WHEN f.freight_value > f.price THEN 1 ELSE 0 END)
        AS items_freight_exceeds_price,
    ROUND(100.0 * SUM(CASE WHEN f.freight_value > f.price THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS pct_items_freight_exceeds_price
FROM fact_order_items f
LEFT JOIN dim_product p ON p.product_id = f.product_id
GROUP BY COALESCE(NULLIF(p.product_category_name, ''), '(no category)')
ORDER BY freight_brl DESC;
