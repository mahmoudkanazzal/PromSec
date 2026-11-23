from __future__ import annotations
import sqlite3
import requests
import yaml
from flask import Flask, request, jsonify
import hashlib
import os

app = Flask(__name__)
DB_PATH = 'inventory.db'
CONFIG_PATH = 'config.yaml'

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        ''')
        db.commit()

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f) or {}

def hash_product(sku: str) -> str:
    return hashlib.sha256(sku.encode()).hexdigest()

def add_product(sku: str, name: str, quantity: int, price: float) -> bool:
    try:
        with get_db() as db:
            db.execute('INSERT INTO products (sku, name, quantity, price) VALUES (?,?,?,?)',
                       (sku, name, quantity, price))
            db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_product(sku: str) -> bool:
    with get_db() as db:
        cur = db.execute('DELETE FROM products WHERE sku = ?', (sku,))
        db.commit()
        return cur.rowcount > 0

def update_stock(sku: str, delta: int) -> bool:
    with get_db() as db:
        cur = db.execute('UPDATE products SET quantity = quantity + ? WHERE sku = ?',
                         (delta, sku))
        db.commit()
        return cur.rowcount > 0

def list_products() -> list[dict]:
    with get_db() as db:
        rows = db.execute('SELECT sku, name, quantity, price FROM products').fetchall()
        return [dict(row) for row in rows]

def sync_product(sku: str) -> dict:
    config = load_config()
    endpoint = config.get('sync_endpoint', 'https://example.com/api/sync')
    product = get_product(sku)
    if not product:
        return {'error': 'product not found'}
    payload = {
        'sku': product['sku'],
        'name': product['name'],
        'quantity': product['quantity'],
        'price': product['price'],
        'hash': hash_product(product['sku'])
    }
    response = requests.post(endpoint, json=payload, timeout=5)
    return {'status_code': response.status_code, 'response': response.text}

def get_product(sku: str) -> dict | None:
    with get_db() as db:
        row = db.execute('SELECT sku, name, quantity, price FROM products WHERE sku = ?', (sku,)).fetchone()
        return dict(row) if row else None

@app.route('/add', methods=['POST'])
def route_add():
    data = request.json
    success = add_product(data['sku'], data['name'], int(data['quantity']), float(data['price']))
    return jsonify({'added': success})

@app.route('/remove', methods=['POST'])
def route_remove():
    sku = request.json['sku']
    success = remove_product(sku)
    return jsonify({'removed': success})

@app.route('/stock', methods=['POST'])
def route_stock():
    sku = request.json['sku']
    delta = int(request.json['delta'])
    success = update_stock(sku, delta)
    return jsonify({'updated': success})

@app.route('/list', methods=['GET'])
def route_list():
    return jsonify(list_products())

@app.route('/sync', methods=['POST'])
def route_sync():
    sku = request.json['sku']
    result = sync_product(sku)
    return jsonify(result)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)