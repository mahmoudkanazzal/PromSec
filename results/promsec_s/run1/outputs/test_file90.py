import os
from flask import Flask, request, redirect
import MySQLdb

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

app = Flask(__name__)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Products WHERE Name = %s", (name,))
        if cur.fetchone():
            return redirect('./add_product')
        cur.execute("INSERT INTO Products (Name, Price) VALUES (%s, %s)", (name, price))
        conn.commit()
        return redirect('./view_products')
    finally:
        cur.close()
        conn.close()

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name')
    new_price = request.form.get('price')
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE Products SET Price = %s WHERE Name = %s", (new_price, name))
        conn.commit()
        return "Price updated successfully"
    finally:
        cur.close()
        conn.close()

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name')
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM Products WHERE Name = %s", (name,))
        conn.commit()
        return "Product deleted successfully"
    finally:
        cur.close()
        conn.close()

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Products WHERE Name LIKE %s", (pattern,))
        rows = cur.fetchall()
        return str(rows)
    finally:
        cur.close()
        conn.close()

@app.route('/view_products', methods=['GET'])
def view_products():
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Products")
        rows = cur.fetchall()
        return str(rows)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)