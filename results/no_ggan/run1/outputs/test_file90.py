import os
from flask import Flask, request, redirect, abort
import MySQLdb

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'test')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')

app = Flask(__name__)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    if not name:
        abort(400, description='Product name cannot be empty')
    try:
        price_val = float(price)
    except ValueError:
        abort(400, description='Invalid price')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT 1 FROM Products WHERE Name = %s', (name,))
            if cur.fetchone():
                return redirect(request.path)
            cur.execute('INSERT INTO Products (Name, Price) VALUES (%s, %s)', (name, price_val))
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return redirect('/view_products')

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    if not name:
        abort(400, description='Product name cannot be empty')
    try:
        price_val = float(price)
    except ValueError:
        abort(400, description='Invalid price')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('UPDATE Products SET Price = %s WHERE Name = %s', (price_val, name))
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return 'Price updated successfully'

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name', '').strip()
    if not name:
        abort(400, description='Product name cannot be empty')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('DELETE FROM Products WHERE Name = %s', (name,))
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return 'Product deleted successfully'

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('term', '')
    pattern = f'%{term}%'
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM Products WHERE Name LIKE %s', (pattern,))
            rows = cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()
    return str(rows)

@app.route('/view_products', methods=['GET'])
def view_products():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM Products')
            rows = cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()
    return str(rows)

if __name__ == '__main__':
    app.run(debug=False)