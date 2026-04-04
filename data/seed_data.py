"""
seed_data.py
------------
Populates the database with realistic sample data for demonstration.
"""

import random
from datetime import datetime, timedelta
from core.database import DatabaseManager

random.seed(42)

FIRST_NAMES = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda",
               "William","Barbara","David","Susan","Richard","Jessica","Joseph","Sarah",
               "Thomas","Karen","Charles","Lisa","Christopher","Nancy","Daniel","Betty",
               "Matthew","Margaret","Anthony","Sandra","Mark","Ashley"]

LAST_NAMES  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
               "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
               "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White"]

CITIES      = ["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia",
               "San Antonio","San Diego","Dallas","San Jose","Austin","Jacksonville"]

COUNTRIES   = ["US","UK","CA","AU","DE","FR","JP","BR"]

CATEGORIES  = ["Electronics","Clothing","Books","Home & Garden","Sports","Toys",
               "Health & Beauty","Food & Beverage","Automotive","Office Supplies"]

DEPARTMENTS = [
    ("Engineering",    850000, "Floor 3"),
    ("Sales",          400000, "Floor 1"),
    ("Marketing",      300000, "Floor 2"),
    ("HR",             200000, "Floor 2"),
    ("Finance",        250000, "Floor 4"),
    ("Customer Service",150000,"Floor 1"),
]

SUPPLIERS = [
    ("TechGlobal Inc",   "orders@techglobal.com",  "+1-555-0101", "US",  4.8),
    ("FashionWorld",     "supply@fashionworld.com", "+44-20-0102", "UK",  4.2),
    ("BookSource",       "info@booksource.com",     "+1-555-0103", "US",  4.5),
    ("HomeGoods Co",     "trade@homegoods.com",     "+1-555-0104", "US",  4.0),
    ("SportsPro",        "wholesale@sportspro.com", "+49-30-0105", "DE",  4.7),
    ("ToyMakers Ltd",    "orders@toymakers.com",    "+81-3-0106",  "JP",  4.3),
    ("HealthFirst",      "supply@healthfirst.com",  "+1-555-0107", "US",  4.6),
    ("FoodDistrib",      "trade@fooddistrib.com",   "+33-1-0108",  "FR",  3.9),
]

PRODUCT_TEMPLATES = [
    # (name, category, price, cost, sku_prefix)
    ("Wireless Bluetooth Headphones",   "Electronics",     89.99,  35.00, "ELEC"),
    ("4K Ultra HD Smart TV 55\"",       "Electronics",    499.99, 280.00, "ELEC"),
    ("Mechanical Gaming Keyboard",      "Electronics",     69.99,  28.00, "ELEC"),
    ("USB-C Charging Hub 7-Port",       "Electronics",     45.99,  15.00, "ELEC"),
    ("Noise Cancelling Earbuds",        "Electronics",    129.99,  50.00, "ELEC"),
    ("Men's Running Shoes",             "Sports",          79.99,  30.00, "SPRT"),
    ("Yoga Mat Premium",                "Sports",          34.99,  12.00, "SPRT"),
    ("Adjustable Dumbbell Set",         "Sports",         149.99,  65.00, "SPRT"),
    ("Resistance Band Kit",             "Sports",          24.99,   8.00, "SPRT"),
    ("Python Programming Guide",        "Books",           39.99,   8.00, "BOOK"),
    ("Data Science Handbook",           "Books",           44.99,   9.00, "BOOK"),
    ("Clean Code",                      "Books",           34.99,   7.00, "BOOK"),
    ("The Art of War",                  "Books",           12.99,   2.00, "BOOK"),
    ("Cotton Crew Neck T-Shirt",        "Clothing",        24.99,   7.00, "CLTH"),
    ("Slim Fit Chino Pants",            "Clothing",        49.99,  16.00, "CLTH"),
    ("Winter Parka Jacket",             "Clothing",       129.99,  50.00, "CLTH"),
    ("Ceramic Coffee Mug Set",          "Home & Garden",   29.99,   9.00, "HOME"),
    ("Stainless Steel Water Bottle",    "Home & Garden",   22.99,   7.00, "HOME"),
    ("Bamboo Cutting Board",            "Home & Garden",   18.99,   5.00, "HOME"),
    ("Multivitamin Daily Pack",         "Health & Beauty", 19.99,   5.00, "HLTH"),
    ("Vitamin D3 Supplements",          "Health & Beauty", 14.99,   3.50, "HLTH"),
    ("Natural Face Moisturiser",        "Health & Beauty", 28.99,   9.00, "HLTH"),
    ("LEGO Classic Brick Box",          "Toys",            49.99,  20.00, "TOYS"),
    ("Board Game Strategy Pack",        "Toys",            34.99,  12.00, "TOYS"),
    ("Car Phone Mount Magnetic",        "Automotive",      19.99,   5.00, "AUTO"),
]


def seed_all(db: DatabaseManager):
    print("\n  Seeding database...")

    dept_ids     = _seed_departments(db)
    supplier_ids = _seed_suppliers(db)
    employee_ids = _seed_employees(db, dept_ids)
    product_ids  = _seed_products(db, supplier_ids)
    _seed_inventory(db, product_ids)
    customer_ids = _seed_customers(db)
    _seed_orders(db, customer_ids, employee_ids, product_ids)

    print("  Seeding complete!")


def _seed_departments(db):
    ids = []
    for name, budget, location in DEPARTMENTS:
        rid = db.execute_write(
            "INSERT OR IGNORE INTO departments (name, budget, location) VALUES (?,?,?)",
            (name, budget, location)
        )
        rows = db.execute_query("SELECT department_id FROM departments WHERE name=?", (name,))
        ids.append(rows[0]["department_id"])
    print(f"    Departments : {len(ids)}")
    return ids


def _seed_suppliers(db):
    ids = []
    for name, email, phone, country, rating in SUPPLIERS:
        db.execute_write(
            "INSERT OR IGNORE INTO suppliers (name, contact_email, phone, country, rating) VALUES (?,?,?,?,?)",
            (name, email, phone, country, rating)
        )
        rows = db.execute_query("SELECT supplier_id FROM suppliers WHERE name=?", (name,))
        ids.append(rows[0]["supplier_id"])
    print(f"    Suppliers   : {len(ids)}")
    return ids


def _seed_employees(db, dept_ids):
    employees = []
    for i in range(50):
        fn   = random.choice(FIRST_NAMES)
        ln   = random.choice(LAST_NAMES)
        email = f"{fn.lower()}.{ln.lower()}{i}@company.com"
        hire  = (datetime(2018,1,1) + timedelta(days=random.randint(0,2000))).strftime("%Y-%m-%d")
        sal   = round(random.uniform(40000, 120000), 2)
        dept  = random.choice(dept_ids)
        db.execute_write(
            "INSERT OR IGNORE INTO employees (first_name,last_name,email,hire_date,salary,department_id) VALUES (?,?,?,?,?,?)",
            (fn, ln, email, hire, sal, dept)
        )
        rows = db.execute_query("SELECT employee_id FROM employees WHERE email=?", (email,))
        if rows:
            employees.append(rows[0]["employee_id"])
    print(f"    Employees   : {len(employees)}")
    return employees


def _seed_products(db, supplier_ids):
    ids = []
    for i, (name, category, price, cost, sku_pfx) in enumerate(PRODUCT_TEMPLATES):
        sku = f"{sku_pfx}-{1000+i:04d}"
        supplier = random.choice(supplier_ids)
        db.execute_write(
            "INSERT OR IGNORE INTO products (name, category, price, cost, sku, supplier_id) VALUES (?,?,?,?,?,?)",
            (name, category, price, cost, sku, supplier)
        )
        rows = db.execute_query("SELECT product_id FROM products WHERE sku=?", (sku,))
        if rows:
            ids.append(rows[0]["product_id"])
    print(f"    Products    : {len(ids)}")
    return ids


def _seed_inventory(db, product_ids):
    for pid in product_ids:
        qty     = random.randint(0, 200)
        reorder = random.randint(5, 20)
        db.execute_write(
            "INSERT OR IGNORE INTO inventory (product_id, quantity, reorder_level, reorder_qty) VALUES (?,?,?,?)",
            (pid, qty, reorder, random.randint(20, 100))
        )
    print(f"    Inventory   : {len(product_ids)} records")


def _seed_customers(db):
    ids = []
    for i in range(200):
        fn      = random.choice(FIRST_NAMES)
        ln      = random.choice(LAST_NAMES)
        email   = f"{fn.lower()}.{ln.lower()}{i}@email.com"
        city    = random.choice(CITIES)
        country = random.choice(COUNTRIES)
        points  = random.randint(0, 5000)
        db.execute_write(
            "INSERT OR IGNORE INTO customers (first_name,last_name,email,city,country,loyalty_points) VALUES (?,?,?,?,?,?)",
            (fn, ln, email, city, country, points)
        )
        rows = db.execute_query("SELECT customer_id FROM customers WHERE email=?", (email,))
        if rows:
            ids.append(rows[0]["customer_id"])
    print(f"    Customers   : {len(ids)}")
    return ids


def _seed_orders(db, customer_ids, employee_ids, product_ids):
    statuses = ["delivered","delivered","delivered","shipped","processing","pending","cancelled"]
    order_count = 0
    item_count  = 0

    for _ in range(500):
        cust     = random.choice(customer_ids)
        emp      = random.choice(employee_ids)
        status   = random.choice(statuses)
        discount = random.choice([0, 0, 0, 0.05, 0.10])
        days_ago = random.randint(1, 730)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")

        shipped   = None
        delivered = None
        if status in ("shipped","delivered"):
            shipped   = (datetime.now() - timedelta(days=days_ago-3)).strftime("%Y-%m-%d")
        if status == "delivered":
            delivered = (datetime.now() - timedelta(days=days_ago-7)).strftime("%Y-%m-%d")

        oid = db.execute_write(
            """INSERT INTO orders
               (customer_id,employee_id,status,discount,order_date,shipped_date,delivered_date)
               VALUES (?,?,?,?,?,?,?)""",
            (cust, emp, status, discount, order_date, shipped, delivered)
        )
        order_count += 1

        # Add 1-5 items per order
        chosen_products = random.sample(product_ids, min(random.randint(1,5), len(product_ids)))
        for pid in chosen_products:
            # Get actual product price
            p = db.execute_query("SELECT price FROM products WHERE product_id=?", (pid,))
            if not p:
                continue
            price = p[0]["price"]
            qty   = random.randint(1, 5)
            item_disc = random.choice([0, 0, 0.05])
            try:
                db.execute_write(
                    "INSERT OR IGNORE INTO order_items (order_id,product_id,quantity,unit_price,discount) VALUES (?,?,?,?,?)",
                    (oid, pid, qty, price, item_disc)
                )
                item_count += 1
            except Exception:
                pass

    print(f"    Orders      : {order_count}")
    print(f"    Order Items : {item_count}")
