-- FLAGSHIP 1 — star schema, step 1 (31 Oct 2026). Schema only; no analysis yet.
-- Grain: fact_order_items = one row per item in an order (Olist order_items grain).
-- Loads into SQLite as written; PostgreSQL needs only type tweaks (TEXT stays TEXT).
-- Column names follow the public Olist Brazilian e-commerce dataset so the
-- ingest step maps source -> star without renaming surprises.
CREATE TABLE dim_customer (
    customer_id TEXT PRIMARY KEY,        -- Olist customers.customer_id
    customer_unique_id TEXT NOT NULL,    -- repeat buyer key for cohorts/RFM
    customer_state TEXT,
    customer_city TEXT
);
CREATE TABLE dim_product (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_weight_g REAL,
    product_length_cm REAL,
    product_height_cm REAL,
    product_width_cm REAL
);
CREATE TABLE dim_seller (
    seller_id TEXT PRIMARY KEY,
    seller_state TEXT,
    seller_city TEXT
);
CREATE TABLE dim_date (
    date_id TEXT PRIMARY KEY,             -- 'YYYY-MM-DD'
    order_year INTEGER NOT NULL,
    order_month INTEGER NOT NULL,
    order_quarter INTEGER NOT NULL
);
CREATE TABLE fact_order_items (
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    customer_id TEXT NOT NULL REFERENCES dim_customer(customer_id),
    product_id TEXT NOT NULL REFERENCES dim_product(product_id),
    seller_id TEXT NOT NULL REFERENCES dim_seller(seller_id),
    date_id TEXT NOT NULL REFERENCES dim_date(date_id),
    price REAL NOT NULL CHECK (price >= 0),
    freight_value REAL NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);
-- Cohort/RFM and revenue queries build on this schema in the week of 9 Nov;
-- the ingest script (week of 2 Nov) loads Olist into staging first, then
-- into these tables, with DQ checks before any analysis runs.
