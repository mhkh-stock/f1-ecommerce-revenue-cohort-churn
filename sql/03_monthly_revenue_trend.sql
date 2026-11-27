-- 03 — Monthly revenue trend (Phase A, revenue leak pack)
-- Business question: is revenue growing, flat, or leaking month to month?
-- Grain: one row per calendar month. Revenue = SUM(price) over fact
-- rows; freight is reported separately, never added to revenue.
-- Month-on-month growth uses LAG() so a single strong month is never
-- mistaken for a trend.
-- Verified on data/processed/f1.db (112,650 fact rows).

SELECT
    d.order_year  AS year,
    d.order_month AS month,
    COUNT(DISTINCT f.order_id) AS orders,
    COUNT(*) AS items,
    ROUND(SUM(f.price), 2) AS revenue_brl,
    ROUND(SUM(f.freight_value), 2) AS freight_brl,
    ROUND(SUM(f.price) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value_brl,
    ROUND(
        100.0 * (SUM(f.price) - LAG(SUM(f.price)) OVER (ORDER BY d.order_year, d.order_month))
        / LAG(SUM(f.price)) OVER (ORDER BY d.order_year, d.order_month),
        2
    ) AS mom_growth_pct
FROM fact_order_items f
JOIN dim_date d ON d.date_id = f.date_id
GROUP BY d.order_year, d.order_month
ORDER BY d.order_year, d.order_month;
