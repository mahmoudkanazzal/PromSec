import os
from flask import Flask, request, redirect, url_for
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'testuser'),
        passwd=os.getenv('DB_PASS', 'test123'),
        db=os.getenv('DB_NAME', 'PRODUCTDB')
    )

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM Products WHERE name = %s LIMIT 1', (name,))
        if cursor.fetchone():
            return redirect(url_for('add_product'))
        cursor.execute('INSERT INTO Products (name, price) VALUES (%s, %s)', (name, price))
        conn.commit()
        return redirect(url_for('view_products'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Products SET price = %s WHERE name = %s', (price, name))
        conn.commit()
        return 'Price updated successfully'
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name', '').strip()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Products WHERE name = %s', (name,))
        conn.commit()
        return 'Product deleted successfully'
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('term', '').strip()
    pattern = f'%{term}%'
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Products WHERE name LIKE %s', (pattern,))
        rows = cursor.fetchall()
        return str(rows)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_products', methods=['GET'])
def view_products():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Products')
        rows = cursor.fetchall()
        return str(rows)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)