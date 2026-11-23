from __future__ import annotations
import sqlite3
from flask import Flask, request, jsonify
import yaml
import os

CONFIG_PATH = 'config.yaml'
DEFAULT_CONFIG = {'db_path': 'inventory.db'}

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    else:
        return DEFAULT_CONFIG

config = load_config()
DB_PATH = config.get('db_path', DEFAULT_CONFIG['db_path'])

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

app = Flask(__name__)

@app.route('/items', methods=['GET'])
def list_items():
    conn = get_db()
    rows = conn.execute('SELECT * FROM items').fetchall()
    items = [dict(row) for row in rows]
    conn.close()
    return jsonify(items)

@app.route('/item', methods=['POST'])
def add_item():
    data = request.get_json()
    name = data.get('name')
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0.0))
    conn = get_db()
    conn.execute(
        'INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)',
        (name, quantity, price)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'added'}), 201

@app.route('/item/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'no data'}), 400
    conn = get_db()
    updated = False
    if 'name' in data:
        conn.execute('UPDATE items SET name = ? WHERE id = ?', (data['name'], item_id))
        updated = True
    if 'quantity' in data:
        conn.execute('UPDATE items SET quantity = ? WHERE id = ?', (int(data['quantity']), item_id))
        updated = True
    if 'price' in data:
        conn.execute('UPDATE items SET price = ? WHERE id = ?', (float(data['price']), item_id))
        updated = True
    if not updated:
        conn.close()
        return jsonify({'error': 'no fields'}), 400
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/item/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    conn = get_db()
    conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)