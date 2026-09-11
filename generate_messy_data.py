"""
generate_messy_data.py
-----------------------
Creates a realistic *messy* export of ERP-style data (the kind you'd get
if someone exported Customers / Products / Orders straight out of an old
system into Excel with zero cleanup).

This script only creates the "before" data. You are not expected to
understand this file deeply -- it's a data generator, not the lesson.
The real learning is in clean.py and queries.sql.

Run:
    python3 generate_messy_data.py
"""
import csv
import random
from pathlib import Path

random.seed(42)  # reproducible output

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

FIRST_NAMES = ["Ahmed", "Sara", "Mohammed", "Fatimah", "Khalid", "Noura",
               "Abdullah", "Layla", "Omar", "Huda", "Yousef", "Mona"]
LAST_NAMES = ["Al-Otaibi", "Al-Ghamdi", "Al-Qahtani", "Al-Harbi", "Al-Zahrani",
              "Al-Dosari", "Al-Shehri", "Al-Mutairi"]
CITIES = ["Khobar", "khobar", "AL KHOBAR", "Dammam", "dammam", "Jubail",
          "Riyadh", "Riyadh ", " Dammam"]
PRODUCT_NAMES = ["Office Chair", "Laptop Stand", "A4 Paper Ream", "Whiteboard",
                  "Desk Lamp", "USB Cable", "Wireless Mouse", "Filing Cabinet",
                  "Printer Toner", "Conference Table"]
CATEGORIES = ["Furniture", "Electronics", "Stationery", "furniture", "ELECTRONICS"]


def messy_phone():
    n = "".join(str(random.randint(0, 9)) for _ in range(9))
    style = random.choice(["05{}", "9665{}", "+9665{}", "05 {}"])
    return style.format(n[1:] if style != "05{}" else n)


def generate_customers(n=60):
    rows = []
    for i in range(1, n + 1):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        # inject messiness: duplicates, missing fields, inconsistent casing
        city = random.choice(CITIES)
        phone = messy_phone() if random.random() > 0.08 else ""
        email = f"{name.lower().replace(' ', '.')}@example.com" if random.random() > 0.15 else ""
        rows.append({
            "customer_id": i,
            "customer_name": name if random.random() > 0.05 else name.upper(),
            "city": city,
            "phone": phone,
            "email": email,
        })
    # inject a handful of near-duplicate rows (common real-world mess)
    for _ in range(5):
        dup = random.choice(rows).copy()
        dup["customer_id"] = n + _ + 1
        rows.append(dup)
    return rows


def generate_products(n=40):
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "product_id": i,
            "product_name": random.choice(PRODUCT_NAMES),
            "category": random.choice(CATEGORIES),
            "unit_price": round(random.uniform(15, 1500), 2) if random.random() > 0.05 else "",
            "stock_qty": random.randint(-5, 300),  # negative = data-entry bug, on purpose
        })
    return rows


def generate_orders(customers, products, n=260):
    rows = []
    for i in range(1, n + 1):
        cust = random.choice(customers)
        prod = random.choice(products)
        qty = random.randint(1, 12)
        date_style = random.choice(["2026-{:02d}-{:02d}", "{:02d}/{:02d}/2026", "{:02d}-{:02d}-2026"])
        m, d = random.randint(1, 8), random.randint(1, 28)
        order_date = date_style.format(m, d) if "2026-" in date_style else date_style.format(d, m)
        rows.append({
            "order_id": i,
            "customer_id": cust["customer_id"],
            "product_id": prod["product_id"],
            "quantity": qty if random.random() > 0.03 else "",
            "order_date": order_date,
            "status": random.choice(["Delivered", "delivered", "DELIVERED", "Pending",
                                       "pending", "Cancelled", "cancelled"]),
        })
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers, products)

    write_csv(RAW_DIR / "customers.csv", customers,
               ["customer_id", "customer_name", "city", "phone", "email"])
    write_csv(RAW_DIR / "products.csv", products,
               ["product_id", "product_name", "category", "unit_price", "stock_qty"])
    write_csv(RAW_DIR / "orders.csv", orders,
               ["order_id", "customer_id", "product_id", "quantity", "order_date", "status"])

    print(f"Generated {len(customers)} customers, {len(products)} products, {len(orders)} orders")
    print(f"Files written to: {RAW_DIR}")
