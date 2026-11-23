import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'PRODUCTDB')
    return MySQLdb.connect(host=host, user=user, password=password, db=db, charset='utf8mb4')

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    if not name or not price:
        return redirect('./add_product')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM products WHERE name = %s", (name,))
        if cur.fetchone():
            return redirect('./add_product')
        cur.execute("INSERT INTO products (name, price) VALUES (%s, %s)", (name, price))
        conn.commit()
        return redirect('./view_products')
    except Exception:
        return "An error occurred", 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name')
    price = request.form.get('price')
    if not name or not price:
        return "Missing parameters", 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE products SET price = %s WHERE name = %s", (price, name))
        conn.commit()
        return "Price updated successfully"
    except Exception:
        return "An error occurred", 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name')
    if not name:
        return "Missing name", 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE name = %s", (name,))
        conn.commit()
        return "Product deleted successfully"
    except Exception:
        return "An error occurred", 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('term', '')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        like_pattern = f"%{term}%"
        cur.execute("SELECT name, price FROM products WHERE name LIKE %s", (like_pattern,))
        rows = cur.fetchall()
        return str(rows)
    except Exception:
        return "An error occurred", 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_products', methods=['GET'])
def view_products():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, price FROM products")
        rows = cur.fetchall()
        return str(rows)
    except Exception:
        return "An error occurred", 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)