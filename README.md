# ERP Data Cleaning & SQL Pipeline

A hands-on project that takes a messy, realistic ERP-style data export
(customers, products, orders — the kind you'd actually get dumped out of
an old system into Excel) and turns it into a clean, queryable SQLite
database, with a guided set of SQL queries that go from basics to the
exact reports a small-business ERP dashboard needs.

**This is a learning project, not a finished product.** It exists so I
can point at every line and explain why it's there — that's the goal,
not just having a green checkmark on GitHub.

## Why this project

Most entry-level ERP/Data roles in the Eastern Province ask for exactly
this: take messy business data, clean it, and answer questions about it
in SQL. This project is a self-contained practice ground for that,
built as part of my learning plan toward Odoo + SQL + Power BI.

## What's inside

| File | What it does |
|---|---|
| `generate_messy_data.py` | Creates a synthetic "before" dataset with realistic mess: inconsistent casing, mixed phone/date formats, duplicate customers, missing values, negative stock |
| `clean.py` | The core lesson — cleans each table step by step, with a comment explaining *why* each fix exists, then loads the result into `erp.db` (SQLite) |
| `queries.sql` | A guided SQL study path: 01 basics → 02 filtering → 03 joins → 04 aggregation → 05 subqueries → 06 the three "report" queries that map directly to a Sales / Inventory / Purchasing dashboard |
| `data/raw/` | The messy "before" CSVs |
| `data/clean/` | The cleaned "after" CSVs |

## How to run it

```bash
pip install pandas
python3 generate_messy_data.py   # creates data/raw/*.csv
python3 clean.py                  # cleans it, creates erp.db
sqlite3 erp.db                    # then paste queries from queries.sql, one at a time
```

## What I'm using this to learn

- Why raw business data is never clean, and what "clean" actually means
  in practice (consistent formats, explicit missing values, flagged —
  not silently deleted — duplicates and referential-integrity issues)
- SQL from `SELECT` through `JOIN`, `GROUP BY`, and subqueries
- How a cleaning script and a set of SQL reports are really the same
  skill applied at two different stages of a data pipeline

## Next steps (as I progress through my learning plan)

- Move this from SQLite to PostgreSQL (matches what Odoo uses)
- Connect Power BI directly to the Postgres version for a live dashboard
- Feed data exported from a real Odoo instance instead of synthetic data
