import os
from flask import Flask, request, redirect, url_for
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'PRODUCTDB')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    if not name or not price:
        return redirect(request.url)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM Products WHERE Name = %s", (name,))
        if cursor.fetchone():
            return redirect(request.url)
        cursor.execute("INSERT INTO Products (Name, Price) VALUES (%s, %s)", (name, price))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect('/view_products')

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    if not name or not price:
        return "Invalid input", 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Products SET Price = %s WHERE Name = %s", (price, name))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return "Price updated successfully"

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name', '').strip()
    if not name:
        return "Invalid input", 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Products WHERE Name = %s", (name,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return "Product deleted successfully"

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('term', '').strip()
    pattern = f"%{term}%"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Products WHERE Name LIKE %s", (pattern,))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return str(rows)

@app.route('/view_products', methods=['GET'])
def view_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Products")
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return str(rows)

if __name__ == '__main__':
    app.run(debug=False)