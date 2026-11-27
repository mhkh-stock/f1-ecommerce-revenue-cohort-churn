-- 07 — Item price distribution (Phase A, revenue leak pack)
-- Business question: is this a low-ticket business where freight and
-- fees dominate, or a high-ticket one?
-- Buckets are on item price (BRL). Averages alone would hide the
-- shape; the bucket shares show it.
-- Verified on data/processed/f1.db (112,650 fact rows).

SELECT
    CASE
        WHEN f.price < 50 THEN 'under 50'
        WHEN f.price < 100 THEN '50-99.99'
        WHEN f.price < 200 THEN '100-199.99'
        WHEN f.price < 500 THEN '200-499.99'
        ELSE '500+'
    END AS price_band_brl,
    COUNT(*) AS items,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS item_share_pct,
    ROUND(SUM(f.price), 2) AS revenue_brl,
    ROUND(100.0 * SUM(f.price) / SUM(SUM(f.price)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(f.price), 2) AS avg_price_brl
FROM fact_order_items f
GROUP BY price_band_brl
ORDER BY MIN(f.price);
