-- 06 — Freight burden (Phase A, revenue leak pack)
-- Business question: where does delivery cost eat the sale?
-- Freight is a cost, not revenue: an order whose freight exceeds its
-- price is a loss-making delivery before any other cost is counted.
-- Bands are on freight as a share of item price.
-- Verified on data/processed/f1.db (112,650 fact rows).

SELECT
    CASE
        WHEN f.freight_value > f.price THEN 'freight exceeds price (>100%)'
        WHEN f.freight_value >= 0.5 * f.price THEN 'high (50-100%)'
        WHEN f.freight_value >= 0.2 * f.price THEN 'moderate (20-50%)'
        ELSE 'low (<20%)'
    END AS freight_band,
    COUNT(*) AS items,
    ROUND(SUM(f.price), 2) AS revenue_brl,
    ROUND(SUM(f.freight_value), 2) AS freight_brl,
    ROUND(100.0 * SUM(f.freight_value) / SUM(f.price), 2) AS freight_as_pct_of_price
FROM fact_order_items f
WHERE f.price > 0
GROUP BY freight_band
ORDER BY freight_brl DESC;

-- Overall freight burden, for the headline number:
-- SELECT ROUND(100.0 * SUM(freight_value) / SUM(price), 2)
-- FROM fact_order_items WHERE price > 0;
