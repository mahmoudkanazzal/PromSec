from __future__ import annotations

import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = 'inventory.db'

def service_login(user: str, password: str) -> bool:
    # Placeholder authentication logic
    return True

def get_db():
    # Retrieve the database password from an environment variable instead of hardcoding it
    db_password = os.getenv('INVENTORY_DB_PASSWORD')
    if db_password is None:
        raise RuntimeError('Database password not set in environment variable INVENTORY_DB_PASSWORD')
    service_login(user='inventory', password=db_password)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

@app.route('/items', methods=['GET'])
def list_items():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM items')
    rows = cur.fetchall()
    items = [dict(row) for row in rows]
    conn.close()
    return jsonify(items)

@app.route('/items', methods=['POST'])
def add_item():
    data = request.get_json()
    name = data.get('name')
    quantity = data.get('quantity', 0)
    price = data.get('price', 0.0)
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)',
                (name, quantity, price))
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return jsonify({'id': item_id, 'name': name, 'quantity': quantity, 'price': price}), 201

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    quantity = data.get('quantity')
    price = data.get('price')
    conn = get_db()
    cur = conn.cursor()
    if quantity is not None:
        cur.execute('UPDATE items SET quantity = ? WHERE id = ?', (quantity, item_id))
    if price is not None:
        cur.execute('UPDATE items SET price = ? WHERE id = ?', (price, item_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    init_db()
    # Run with debug mode disabled by default; can be enabled via environment variable
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode)