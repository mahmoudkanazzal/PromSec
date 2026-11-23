from __future__ import annotations
import sqlite3
from flask import Flask, request, jsonify, g
import os

app = Flask(__name__)
DATABASE = 'shop.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL)''')
        conn.commit()
        conn.close()

def add_item(name: str, quantity: int, price: float):
    db = get_db()
    db.execute('INSERT INTO inventory (name, quantity, price) VALUES (?, ?, ?)',
               (name, quantity, price))
    db.commit()
    return jsonify({'status': 'added'})

def update_quantity(item_id: int, delta: int):
    db = get_db()
    db.execute('UPDATE inventory SET quantity = quantity + ? WHERE id = ?',
               (delta, item_id))
    db.commit()
    return jsonify({'status': 'updated'})

def search_items(name: str):
    db = get_db()
    query = "SELECT * FROM inventory WHERE name LIKE ?"
    param = f"%{name}%"
    cur = db.execute(query, (param,))
    rows = [dict(row) for row in cur.fetchall()]
    return jsonify(rows)

def list_items():
    db = get_db()
    cur = db.execute('SELECT * FROM inventory')
    rows = [dict(row) for row in cur.fetchall()]
    return jsonify(rows)

@app.route('/add', methods=['POST'])
def route_add():
    name = request.form.get('name', '')
    qty = int(request.form.get('quantity', '0'))
    price = float(request.form.get('price', '0.0'))
    return add_item(name, qty, price)

@app.route('/update', methods=['POST'])
def route_update():
    item_id = int(request.form.get('id', '0'))
    delta = int(request.form.get('delta', '0'))
    return update_quantity(item_id, delta)

@app.route('/search')
def route_search():
    name = request.args.get('name', '')
    return search_items(name)

@app.route('/list')
def route_list():
    return list_items()

if __name__ == '__main__':
    init_db()
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)