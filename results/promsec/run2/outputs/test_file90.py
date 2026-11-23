import os
import mysql.connector
from flask import Flask, request, redirect, url_for, jsonify, abort

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def validate_name(value):
    if not isinstance(value, str):
        abort(400)
    cleaned = value.strip()
    if not cleaned:
        abort(400)
    return cleaned

def validate_price(value):
    try:
        price = float(value)
    except (TypeError, ValueError):
        abort(400)
    if price <= 0:
        abort(400)
    return price

def validate_search_term(value):
    if value is None:
        abort(400)
    if not isinstance(value, str):
        abort(400)
    return value

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    name = validate_name(name)
    price = validate_price(price)
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT id FROM products WHERE name = %s', (name,))
            if cursor.fetchone():
                abort(409)
            cursor.execute('INSERT INTO products (name, price) VALUES (%s, %s)', (name, price))
        conn.commit()
    return redirect(url_for('view_products'))

@app.route('/update_price', methods=['POST'])
def update_price():
    name = request.form.get('name')
    new_price = request.form.get('new_price')
    name = validate_name(name)
    new_price = validate_price(new_price)
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute('UPDATE products SET price = %s WHERE name = %s', (new_price, name))
            if cursor.rowcount == 0:
                abort(404)
        conn.commit()
    return redirect(url_for('view_products'))

@app.route('/delete_product', methods=['POST'])
def delete_product():
    name = request.form.get('name')
    name = validate_name(name)
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute('DELETE FROM products WHERE name = %s', (name,))
            if cursor.rowcount == 0:
                abort(404)
        conn.commit()
    return redirect(url_for('view_products'))

@app.route('/search_products', methods=['GET'])
def search_products():
    term = request.args.get('search_term')
    term = validate_search_term(term)
    pattern = f"%{term}%"
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT id, name, price FROM products WHERE name LIKE %s', (pattern,))
            rows = cursor.fetchall()
    return jsonify(rows)

@app.route('/view_products', methods=['GET'])
def view_products():
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT id, name, price FROM products')
            rows = cursor.fetchall()
    return jsonify(rows)

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=host, port=port, debug=False)