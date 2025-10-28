from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

DB = 'pharm_tally.db'

# -----------------------------
# Helper Functions
# -----------------------------
def get_suppliers():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, name FROM suppliers")
    suppliers = [{"id": row[0], "name": row[1]} for row in c.fetchall()]
    conn.close()
    return suppliers

def get_stock():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, name, brand_name, selling_price, packet_quantity FROM stock")
    stock_list = []
    for row in c.fetchall():
        stock_list.append({
            "id": row[0],
            "name": row[1],
            "brand_name": row[2],
            "selling_price": row[3],
            "packet_quantity": row[4]
        })
    conn.close()
    return stock_list

# -----------------------------
# Routes
# -----------------------------

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Replace with real validation
        if username == "admin" and password == "1234":
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT SUM(total_price) FROM sales")
    total_sales = c.fetchone()[0] or 0
    conn.close()
    return render_template('dashboard.html', total_sales=total_sales)

# Suppliers
@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form.get('email','')
        address = request.form.get('address','')
        contact = request.form['contact']
        location = request.form.get('location','')
        c.execute('''INSERT INTO suppliers (name, email, address, contact, location)
                     VALUES (?, ?, ?, ?, ?)''', (name, email, address, contact, location))
        conn.commit()
        flash(f"Supplier {name} added!")
    c.execute("SELECT * FROM suppliers")
    rows = c.fetchall()
    conn.close()
    return render_template('suppliers.html', suppliers=rows)

# Add Stock
@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    suppliers = get_suppliers()
    if request.method == 'POST':
        name = request.form['name']
        brand_name = request.form['brand_name']
        cost_price = float(request.form['cost_price'])
        packet_quantity = int(request.form['packet_quantity'])
        selling_price = float(request.form['selling_price'])
        if selling_price < cost_price:
            flash("Selling price cannot be lower than cost price")
            return redirect(url_for('add_stock'))
        batch_number = request.form.get('batch_number','')
        dosage_form = request.form.get('dosage_form','')
        supplier_id = int(request.form.get('supplier_id',0))
        expiry_date = request.form.get('expiry_date','')
        strength = request.form.get('strength','')

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('''INSERT INTO stock (name, brand_name, cost_price, packet_quantity, selling_price,
                     batch_number, dosage_form, supplier_id, expiry_date, strength)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (name, brand_name, cost_price, packet_quantity, selling_price,
                   batch_number, dosage_form, supplier_id, expiry_date, strength))
        conn.commit()
        conn.close()
        flash(f"Stock for {name} added!")
        return redirect(url_for('add_stock'))

    stock_list = get_stock()
    return render_template('add_stock.html', stock=stock_list, suppliers=suppliers)

# Sell Out
@app.route('/sell_out', methods=['GET', 'POST'])
def sell_out():
    stock_list = get_stock()
    if request.method == 'POST':
        transaction_id = str(random.randint(100000,999999))
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        # Expecting multiple items: "drug_id:quantity,drug_id:quantity"
        items = request.form.get('items','').split(',')
        total_transaction = 0
        for item in items:
            if not item.strip():
                continue
            drug_id, quantity = item.split(':')
            drug_id = int(drug_id)
            quantity = int(quantity)
            # Get selling price
            c.execute("SELECT selling_price FROM stock WHERE id=?", (drug_id,))
            price = c.fetchone()[0]
            total = price * quantity
            total_transaction += total
            c.execute('''INSERT INTO sales (transaction_id, stock_id, quantity_sold, selling_price, total_price, sale_date)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (transaction_id, drug_id, quantity, price, total, sale_date))
        conn.commit()
        conn.close()
        flash(f"Sold successfully! Transaction ID: {transaction_id}")
        return redirect(url_for('sell_out'))

    return render_template('sell_out.html', stock=stock_list)

# Receipts
@app.route('/receipts')
def receipts():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM sales ORDER BY sale_date DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('receipts.html', sales=rows)

# -----------------------------
# Logout
# -----------------------------
@app.route('/logout')
def logout():
    flash("Logged out successfully!")
    return redirect(url_for('login'))

# -----------------------------

# Run the app
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)


