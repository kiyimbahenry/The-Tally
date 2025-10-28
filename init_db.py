import sqlite3

DB = 'pharm_tally.db'

conn = sqlite3.connect(DB)
c = conn.cursor()

# -----------------------------
# Suppliers Table
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    address TEXT,
    contact TEXT NOT NULL,
    location TEXT
)
''')

# -----------------------------
# Stock Table
# -----------------------------
c.execute('''
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand_name TEXT,
    cost_price REAL NOT NULL,
    packet_quantity INTEGER NOT NULL,
    selling_price REAL NOT NULL,
    batch_number TEXT,
    dosage_form TEXT,
    supplier_id INTEGER,
    expiry_date TEXT,
    strength TEXT,
    FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
)
''')

# -----------------------------
# Sales Table
# -----------------------------
c.execute("DROP TABLE IF EXISTS sales")  # drop old sales table if exists

c.execute('''
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    stock_id INTEGER,
    quantity_sold INTEGER,
    selling_price REAL,
    total_price REAL,
    sale_date TEXT,
    FOREIGN KEY(stock_id) REFERENCES stock(id)
)
''')

conn.commit()
conn.close()
print("Database initialized successfully with all correct columns!")

