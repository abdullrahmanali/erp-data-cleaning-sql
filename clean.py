"""
clean.py — the actual lesson.
------------------------------
Read this file top to bottom, slowly. It takes the messy raw exports in
data/raw/ and turns them into clean tables in a SQLite database
(erp.db) that queries.sql then runs against.

Every step below explains WHY, not just WHAT — that's the difference
between "I ran a script" and "I can explain this in an interview."

Run:
    python3 clean.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent / "data" / "raw"
CLEAN = Path(__file__).parent / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(__file__).parent / "erp.db"


def clean_customers():
    df = pd.read_csv(RAW / "customers.csv")

    # 1) Whitespace and casing are the #1 source of "duplicate" rows that
    #    aren't actually duplicates to a computer. "Khobar" != " khobar ".
    df["city"] = df["city"].str.strip().str.title()

    # 2) Names: normalise casing so "NOURA AL-GHAMDI" and "Noura Al-Ghamdi"
    #    are recognised as the same customer later.
    df["customer_name"] = df["customer_name"].str.strip().str.title()

    # 3) Missing emails/phones: don't guess a value — leave it explicitly
    #    empty (NaN) instead of "" so later SQL/COUNT logic treats it
    #    correctly as "unknown", not as a real value.
    df["email"] = df["email"].replace("", pd.NA)
    df["phone"] = df["phone"].replace("", pd.NA)

    # 4) Phone numbers: strip everything except digits, then normalise to
    #    a single format (9665XXXXXXXX). Real ERP exports mix
    #    "05XXXXXXXX", "+9665XXXXXXXX" and "9665XXXXXXXX" — you cannot
    #    JOIN or de-duplicate on a column with three different formats.
    def normalise_phone(p):
        if pd.isna(p):
            return pd.NA
        digits = "".join(ch for ch in str(p) if ch.isdigit())
        if digits.startswith("05"):
            digits = "966" + digits[1:]
        elif digits.startswith("5"):
            digits = "966" + digits
        return digits

    df["phone"] = df["phone"].apply(normalise_phone)

    # 5) Duplicate customers: the generator deliberately injected a few
    #    near-duplicate rows (same name+city, different customer_id) —
    #    this happens for real when the same client is entered twice.
    #    We flag it rather than silently deleting, because deleting the
    #    wrong one can break historical orders that reference that ID.
    dup_mask = df.duplicated(subset=["customer_name", "city"], keep="first")
    if dup_mask.any():
        print(f"[customers] {dup_mask.sum()} likely duplicate customer(s) found "
              f"(same name+city, different ID) — kept both, flagged in is_duplicate")
    df["is_duplicate"] = dup_mask

    return df


def clean_products():
    df = pd.read_csv(RAW / "products.csv")

    df["category"] = df["category"].str.strip().str.title()

    # Missing price: this is a real decision, not a technical one. We
    # don't invent a price — we leave it NULL so a report can surface
    # "products missing a price" as its own finding, instead of quietly
    # showing 0.00 and skewing revenue numbers.
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Negative stock is a data-entry bug (can't have -3 chairs in a
    # warehouse). We clip it to 0 and keep a flag so it's auditable
    # instead of silently "fixed".
    df["stock_qty_raw"] = df["stock_qty"]
    df["stock_qty"] = df["stock_qty"].clip(lower=0)
    df["had_negative_stock"] = df["stock_qty_raw"] < 0

    return df


def clean_orders(customers_df, products_df):
    df = pd.read_csv(RAW / "orders.csv")

    # Dates came in three different formats depending on who exported
    # them. dayfirst=False/True guesses wrong half the time on mixed
    # data, so instead we try the known formats explicitly.
    def parse_date(s):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return pd.to_datetime(s, format=fmt)
            except (ValueError, TypeError):
                continue
        return pd.NaT

    df["order_date"] = df["order_date"].apply(parse_date)

    # Status: collapse "Delivered/delivered/DELIVERED" into one value.
    df["status"] = df["status"].str.strip().str.capitalize()

    # Missing quantity: an order with no quantity is not a valid order.
    # Rather than silently drop it, count it, then drop it — the count
    # is what you'd mention in the project README/interview.
    missing_qty = df["quantity"].isna() | (df["quantity"] == "")
    print(f"[orders] dropping {missing_qty.sum()} row(s) with missing quantity")
    df = df[~missing_qty].copy()
    df["quantity"] = df["quantity"].astype(int)

    # Referential integrity: every order should point at a real customer
    # and a real product. This is exactly what a JOIN in queries.sql
    # checks later — cleaning and SQL are the same skill from two ends.
    valid_customers = set(customers_df["customer_id"])
    valid_products = set(products_df["product_id"])
    orphaned = df[~df["customer_id"].isin(valid_customers) | ~df["product_id"].isin(valid_products)]
    if len(orphaned):
        print(f"[orders] {len(orphaned)} orphaned order(s) reference a missing customer/product")
    df = df[df["customer_id"].isin(valid_customers) & df["product_id"].isin(valid_products)]

    return df


def main():
    customers = clean_customers()
    products = clean_products()
    orders = clean_orders(customers, products)

    customers.to_csv(CLEAN / "customers.csv", index=False)
    products.to_csv(CLEAN / "products.csv", index=False)
    orders.to_csv(CLEAN / "orders.csv", index=False)

    # Load into SQLite so queries.sql has something to run against.
    # SQLite needs zero setup (no server, one file) which is exactly
    # why it's the right tool for a portfolio project — Postgres later
    # in the plan is a drop-in upgrade of the same SQL you practice here.
    conn = sqlite3.connect(DB_PATH)
    customers.to_sql("customers", conn, if_exists="replace", index=False)
    products.to_sql("products", conn, if_exists="replace", index=False)
    orders.to_sql("orders", conn, if_exists="replace", index=False)
    conn.close()

    print(f"\nDone. Clean CSVs in {CLEAN}, and loaded into {DB_PATH}")
    print(f"Rows: {len(customers)} customers, {len(products)} products, {len(orders)} orders")


if __name__ == "__main__":
    main()
