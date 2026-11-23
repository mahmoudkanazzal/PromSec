import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    return MySQLdb.connect(host='localhost', user=user, passwd=password, db='PRODUCTDB', charset='utf8mb4')

def fetch_all(query, params=()):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return rows
    except MySQLdb.Error:
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def execute_query(query, params=()):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.rowcount
    except MySQLdb.Error:
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    if not name or not price:
        return redirect('./add_product')
    exists = fetch_all('SELECT 1 FROM Products WHERE Name=%s', (name,))
    if exists is None:
        return 'Database error', 500
    if exists:
        return redirect('./add_product')
    result = execute_query('INSERT INTO Products (Name, Price) VALUES (%s, %s)', (name, price))
    if result is None:
        return 'Database error', 500
    return redirect('./view_products')

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name')
    price = request.form.get('price')
    if not name or not price:
        return 'Invalid input', 400
    result = execute_query('UPDATE Products SET Price=%s WHERE Name=%s', (price, name))
    if result is None:
        return 'Database error', 500
    return 'Price updated successfully'

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name')
    if not name:
        return 'Invalid input', 400
    result = execute_query('DELETE FROM Products WHERE Name=%s', (name,))
    if result is None:
        return 'Database error', 500
    return 'Product deleted successfully'

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('term', '')
    like_term = f'%{term}%'
    rows = fetch_all('SELECT Name, Price FROM Products WHERE Name LIKE %s', (like_term,))
    if rows is None:
        return 'Database error', 500
    output = '\n'.join([f'Name: {r[0]}, Price: {r[1]}' for r in rows])
    return output

@app.route('/view_products', methods=['GET'])
def view_products():
    rows = fetch_all('SELECT Name, Price FROM Products')
    if rows is None:
        return 'Database error', 500
    output = '\n'.join([f'Name: {r[0]}, Price: {r[1]}' for r in rows])
    return output

if __name__ == '__main__':
    app.run(debug=False)