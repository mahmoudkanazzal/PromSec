from __future__ import annotations
import sqlite3
from flask import Flask, request, jsonify
import yaml
import os

app = Flask(__name__)
DB_PATH = 'inventory.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
        ''')
        conn.commit()

def add_item_from_yaml(yaml_str: str) -> dict:
    data = yaml.safe_load(yaml_str)  # safe load
    name = data.get('name')
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0.0))
    with get_db() as conn:
        cur = conn.execute(
            'INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)',
            (name, quantity, price)
        )
        conn.commit()
        item_id = cur.lastrowid
    return {'id': item_id, 'name': name, 'quantity': quantity, 'price': price}

def list_items() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM items').fetchall()
    return [dict(row) for row in rows]

def update_quantity(item_id: int, delta: int) -> dict:
    with get_db() as conn:
        conn.execute('UPDATE items SET quantity = quantity + ? WHERE id = ?', (delta, item_id))
        conn.commit()
        row = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    return dict(row) if row else {}

def delete_item(item_id: int) -> bool:
    with get_db() as conn:
        conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
        conn.commit()
    return True

@app.route('/add', methods=['POST'])
def route_add():
    yaml_str = request.data.decode('utf-8')
    item = add_item_from_yaml(yaml_str)
    return jsonify(item), 201

@app.route('/list', methods=['GET'])
def route_list():
    items = list_items()
    return jsonify(items)

@app.route('/update', methods=['POST'])
def route_update():
    payload = request.get_json()
    item_id = payload.get('id')
    delta = payload.get('delta', 0)
    item = update_quantity(item_id, delta)
    return jsonify(item)

@app.route('/delete', methods=['POST'])
def route_delete():
    payload = request.get_json()
    item_id = payload.get('id')
    delete_item(item_id)
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(host='127.0.0.1', port=5000)