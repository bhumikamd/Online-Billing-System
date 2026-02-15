from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = 'secret123'  # Used for session management

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="BHUMIKA@29562",
    database="billing_system"
)
cursor = db.cursor(dictionary=True)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['username']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('dashboard.html', products=products)

@app.route('/add-product', methods=['POST'])
def add_product():
    name = request.form['name']
    price = float(request.form['price'])
    stock = int(request.form['stock'])
    cursor.execute("INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)", (name, price, stock))
    db.commit()
    return redirect('/dashboard')

@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    customer_name = request.form['customer_name']
    product_ids = request.form.getlist('product_id')
    total = 0

    items = []
    for pid in product_ids:

        qty = request.form.get(f"quantity_{pid}")

        if not qty or int(qty) <= 0:
            continue

        cursor.execute("SELECT * FROM products WHERE product_id = %s", (pid,))
        product = cursor.fetchone()

        total += product['price'] * int(qty)
        items.append((pid, int(qty)))

    cursor.execute("INSERT INTO invoices (customer_name, total_amount) VALUES (%s, %s)", (customer_name, total))
    invoice_id = cursor.lastrowid

    for pid, qty in items:
        cursor.execute(
            "INSERT INTO invoice_items (invoice_id, product_id, quantity) VALUES (%s, %s, %s)",
            (invoice_id, pid, qty)
        )

        # decrease stock after purchase
        cursor.execute(
            "UPDATE products SET stock = stock - %s WHERE product_id = %s",
            (qty, pid)
        )

    db.commit()

    return redirect(f"/invoice/{invoice_id}")

@app.route('/invoice/<int:invoice_id>')
def invoice(invoice_id):
    cursor.execute("SELECT * FROM invoices WHERE invoice_id = %s", (invoice_id,))
    invoice = cursor.fetchone()
    cursor.execute("SELECT p.name, p.price, ii.quantity FROM invoice_items ii JOIN products p ON ii.product_id = p.product_id WHERE ii.invoice_id = %s", (invoice_id,))
    items = cursor.fetchall()
    return render_template('invoice.html', invoice=invoice, items=items)
@app.route('/invoices')
def all_invoices():
    cursor.execute("""
        SELECT 
          invoice_id, 
          customer_name, 
          created_at, 
          total_amount
        FROM invoices
        ORDER BY created_at DESC
    """)
    invoices = cursor.fetchall()
    return render_template('invoices.html', invoices=invoices)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
