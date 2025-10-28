import sqlite3

conn = sqlite3.connect('pharm_tally.db')
c = conn.cursor()

# Add columns to stock table
try:
    c.execute("ALTER TABLE stock ADD COLUMN batch_number TEXT")
    print("Added batch_number to stock")
except sqlite3.OperationalError:
    print("Column batch_number already exists in stock")

try:
    c.execute("ALTER TABLE stock ADD COLUMN expiry_date TEXT")
    print("Added expiry_date to stock")
except sqlite3.OperationalError:
    print("Column expiry_date already exists in stock")

# Add column to sales table
try:
    c.execute("ALTER TABLE sales ADD COLUMN transaction_id TEXT")
    print("Added transaction_id to sales")
except sqlite3.OperationalError:
    print("Column transaction_id already exists in sales")

conn.commit()
conn.close()
print("Database schema updated successfully!")
