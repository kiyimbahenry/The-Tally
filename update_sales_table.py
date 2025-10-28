import sqlite3

DB = 'pharm_tally.db'

conn = sqlite3.connect(DB)
c = conn.cursor()

# Drop old sales table
c.execute("DROP TABLE IF EXISTS sales")

# Create new sales table with transaction_id
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
print("Sales table updated successfully!")
