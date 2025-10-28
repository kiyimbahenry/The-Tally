from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, datetime, uuid

app = Flask(__name__)
app.secret_key = 'secret123'

# Initialize database
def init_db():
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()
    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT)''')
    # Add default admin
    c.execute("INSERT OR IGNORE INTO users(id, username, password) VALUES(1,'admin','1234')")
    # Suppliers
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT)''')
    # Stock
    c.execute('''CREATE TABLE IF NOT EXISTS stock(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                quantity INTEGER,
                price REAL,
                supplier_id INTEGER,
                batch_number TEXT,
                expiry_date TEXT)''')
    # Sales
    c.execute('''CREATE TABLE IF NOT EXISTS sales(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT,
                quantity INTEGER,
                total REAL,
                date TEXT,
                batch_number TEXT,
                transaction_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Login
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('pharm_tally.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash('Invalid login')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()
    c.execute("SELECT stock.id, stock.name, stock.quantity, stock.price, suppliers.name, stock.batch_number, stock.expiry_date FROM stock LEFT JOIN suppliers ON stock.supplier_id = suppliers.id")
    items = c.fetchall()
    conn.close()
    return render_template('dashboard.html', items=items)

# Add stock
@app.route('/add_stock', methods=['GET','POST'])
def add_stock():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()
    c.execute("SELECT * FROM suppliers")
    suppliers = c.fetchall()
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        supplier_id = int(request.form['supplier_id'])
        batch_number = request.form['batch_number']
        expiry_date = request.form['expiry_date']
        c.execute("INSERT INTO stock(name,quantity,price,supplier_id,batch_number,expiry_date) VALUES(?,?,?,?,?,?)",
                  (name, quantity, price, supplier_id, batch_number, expiry_date))
        conn.commit()
        conn.close()
        flash("Stock added successfully")
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('add_stock.html', suppliers=suppliers)

# Suppliers
@app.route('/suppliers', methods=['GET','POST'])
def suppliers():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        c.execute("INSERT INTO suppliers(name) VALUES(?)", (name,))
        conn.commit()
    c.execute("SELECT * FROM suppliers")
    supplier_list = c.fetchall()
    conn.close()
    return render_template('suppliers.html', suppliers=supplier_list)

# Search stock for sell_out
@app.route('/search_stock')
def search_stock():
    name = request.args.get('name')
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()
    c.execute("SELECT name, batch_number, price, quantity FROM stock WHERE name LIKE ? AND quantity>0 LIMIT 1", ('%'+name+'%',))
    item = c.fetchone()
    conn.close()
    if item:
        return jsonify({'name': item[0], 'batch_number': item[1], 'price': item[2], 'quantity': item[3]})
    return jsonify({})

# Sell out (multi-drug cart)
@app.route('/sell_out', methods=['GET','POST'])
def sell_out():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()

    if request.method == 'POST':
        cart = request.json.get('cart')
        if not cart:
            return jsonify({'status':'error','message':'Cart is empty'}),400
        transaction_id = str(uuid.uuid4())
        for product in cart:
            item = product['item']
            quantity = int(product['quantity'])
            batch_number = product['batch_number']
            c.execute("SELECT quantity, price FROM stock WHERE name=? AND batch_number=?", (item, batch_number))
            stock_item = c.fetchone()
            if stock_item and stock_item[0] >= quantity:
                new_quantity = stock_item[0] - quantity
                total = stock_item[1] * quantity
                date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("UPDATE stock SET quantity=? WHERE name=? AND batch_number=?", (new_quantity, item, batch_number))
                c.execute("INSERT INTO sales(item,quantity,total,date,batch_number,transaction_id) VALUES(?,?,?,?,?,?)",
                          (item, quantity, total, date, batch_number, transaction_id))
            else:
                conn.close()
                return jsonify({'status':'error','message':f"Not enough stock for {item} ({batch_number})"}),400
        conn.commit()
        conn.close()
        return jsonify({'status':'success','message':'Sale completed!'})
    
    c.execute("SELECT name, batch_number, price, quantity FROM stock WHERE quantity>0")
    items = c.fetchall()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT SUM(total) FROM sales WHERE date LIKE ?", (f"{today}%",))
    daily_total = c.fetchone()[0] or 0
    conn.close()
    return render_template('sell_out.html', items=items, daily_total=daily_total)

# Receipts page
@app.route('/receipts')
def receipts():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT transaction_id, date FROM sales ORDER BY date DESC")
    transactions = c.fetchall()
    all_transactions = []
    daily_total = 0
    for tx in transactions:
        tx_id, date = tx
        c.execute("SELECT item, quantity, total, batch_number FROM sales WHERE transaction_id=?", (tx_id,))
        items = c.fetchall()
        tx_total = sum([i[2] for i in items])
        daily_total += tx_total
        all_transactions.append({'transaction_id': tx_id, 'date': date, 'items': items, 'tx_total': tx_total})
    conn.close()
    return render_template('receipts.html', all_transactions=all_transactions, daily_total=daily_total)

# Single receipt
@app.route('/receipt/<transaction_id>')
def receipt(transaction_id):
    conn = sqlite3.connect('pharm_tally.db')
    c = conn.cursor()
    c.execute("SELECT item, quantity, total, batch_number, date FROM sales WHERE transaction_id=?", (transaction_id,))
    items = c.fetchall()
    if items:
        date = items[0][4]
        tx_total = sum([i[2] for i in items])
        conn.close()
        return render_template('receipt.html', items=items, total=tx_total, date=date)
    conn.close()
    flash("Transaction not found!")
    return redirect(url_for('receipts'))

if __name__ == '__main__':
    app.run(debug=True)
