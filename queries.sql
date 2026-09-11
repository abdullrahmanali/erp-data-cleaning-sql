-- queries.sql — a guided SQL study path, not just a query dump.
--
-- How to use this file: open erp.db with any SQLite client
-- (e.g. `sqlite3 erp.db`, or the "SQLite Viewer" VS Code extension,
-- or DB Browser for SQLite) and run these ONE AT A TIME, in order.
-- Before running each one, read the comment and guess the output
-- shape first — that's what actually builds the skill.
--
-- Structure: 01 = basics, 02 = filtering, 03 = joins, 04 = aggregation,
-- 05 = subqueries/window-style thinking, 06 = the "report" queries you'd
-- actually show in an interview.

-- ============================================================
-- 01. SELECT basics — look at the raw shape of each table first
-- ============================================================

SELECT * FROM customers LIMIT 10;

SELECT customer_name, city FROM products; -- WRONG ON PURPOSE:
-- this will error ("no such column: customer_name" doesn't exist on
-- products). Run it, read the error message, fix it yourself to
-- SELECT product_name, category FROM products;
-- Reading SQL error messages calmly is 50% of the actual job skill.


-- ============================================================
-- 02. WHERE — filtering rows
-- ============================================================

-- All orders placed with "Cancelled" status
SELECT * FROM orders WHERE status = 'Cancelled';

-- Products that are currently out of stock
SELECT product_name, stock_qty FROM products WHERE stock_qty = 0;

-- Products priced between 100 and 500 (a typical "mid-range" filter
-- you'd be asked for in a real ERP report)
SELECT product_name, unit_price FROM products
WHERE unit_price BETWEEN 100 AND 500
ORDER BY unit_price DESC;

-- Customers with a missing phone number — useful for a data-quality
-- check, which is a real recurring ERP task
SELECT customer_name, city FROM customers WHERE phone IS NULL;


-- ============================================================
-- 03. JOIN — this is the single most important skill in this file
-- ============================================================

-- An order row on its own is almost meaningless (just IDs). JOIN is
-- how you turn "customer_id = 14" into "Ahmed Al-Otaibi".
SELECT
    o.order_id,
    c.customer_name,
    p.product_name,
    o.quantity,
    o.order_date
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
ORDER BY o.order_date
LIMIT 15;

-- LEFT JOIN vs JOIN: find customers who have NEVER placed an order.
-- A plain JOIN would silently hide them — LEFT JOIN keeps them with
-- NULL order columns, which is exactly what "customers with 0 orders"
-- reporting needs.
SELECT c.customer_name, o.order_id
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;


-- ============================================================
-- 04. GROUP BY — aggregation, the heart of every dashboard number
-- ============================================================

-- Total quantity sold per product (this single query is basically
-- the "Inventory" page of the Power BI dashboard from the master plan)
SELECT
    p.product_name,
    SUM(o.quantity) AS total_units_sold,
    COUNT(o.order_id) AS number_of_orders
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'Delivered'
GROUP BY p.product_name
ORDER BY total_units_sold DESC;

-- Revenue per city (JOIN + GROUP BY + a calculated column together —
-- this is the exact shape of query a "Junior Data Analyst" job test
-- will hand you)
SELECT
    c.city,
    ROUND(SUM(o.quantity * p.unit_price), 2) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
WHERE o.status = 'Delivered'
GROUP BY c.city
ORDER BY revenue DESC;

-- Order count by status — a one-line query that answers "how healthy
-- is our order pipeline" (cancellation rate is a real KPI)
SELECT status, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 1) AS pct
FROM orders
GROUP BY status
ORDER BY n DESC;


-- ============================================================
-- 05. Subqueries — "a query inside a query"
-- ============================================================

-- Products that sold above the average quantity (subquery in WHERE)
SELECT product_name, stock_qty FROM products
WHERE product_id IN (
    SELECT product_id FROM orders
    GROUP BY product_id
    HAVING SUM(quantity) > (
        SELECT AVG(qty_per_product) FROM (
            SELECT SUM(quantity) AS qty_per_product
            FROM orders GROUP BY product_id
        )
    )
);
-- This one is deliberately the hardest query in the file. If it
-- takes you 20 minutes to understand, that's normal — read it from
-- the innermost SELECT outward, not top to bottom.


-- ============================================================
-- 06. The three "report" queries — these map directly to the three
--     Power BI dashboard pages in the master plan (Section 4)
-- ============================================================

-- Page 1 — Sales: monthly revenue trend
SELECT
    strftime('%Y-%m', o.order_date) AS month,
    ROUND(SUM(o.quantity * p.unit_price), 2) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'Delivered'
GROUP BY month
ORDER BY month;

-- Page 2 — Inventory: stagnant items (in stock, zero delivered orders)
SELECT p.product_name, p.stock_qty
FROM products p
LEFT JOIN orders o
       ON p.product_id = o.product_id AND o.status = 'Delivered'
WHERE o.order_id IS NULL AND p.stock_qty > 0;

-- Page 3 — Purchasing / customer performance: top 5 customers by spend
SELECT
    c.customer_name,
    ROUND(SUM(o.quantity * p.unit_price), 2) AS total_spent,
    COUNT(DISTINCT o.order_id) AS orders_placed
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
WHERE o.status = 'Delivered'
GROUP BY c.customer_name
ORDER BY total_spent DESC
LIMIT 5;

-- ============================================================
-- Your turn — do not skip this
-- ============================================================
-- Write 3 new queries of your own below, answering:
--   1. Which category of products generates the most revenue?
--   2. Which customers have an email on file but no phone number?
--   3. What percentage of orders are still "Pending"?
-- If you can write these three unaided, you are ready to say
-- "I know SQL" in an interview.
