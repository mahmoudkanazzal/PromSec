from __future__ import annotations
import os
import sqlite3
import subprocess
import shlex
from flask import Flask, request, jsonify, g

APP = Flask(__name__)
DB_PATH = 'inventory.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        qty INTEGER NOT NULL)''')
        conn.commit()

@APP.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_item(name: str, qty: int) -> int:
    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO items (name, qty) VALUES (?, ?)', (name, qty))
    db.commit()
    return cur.lastrowid

def update_item(item_id: int, qty: int) -> bool:
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE items SET qty = ? WHERE id = ?', (qty, item_id))
    db.commit()
    return cur.rowcount > 0

def list_items():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, name, qty FROM items')
    rows = cur.fetchall()
    return [dict(row) for row in rows]

def run_user_command():
    cmd = request.args.get('cmd', '')
    if cmd:
        args = shlex.split(cmd)
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            return jsonify({
                'status': 'executed',
                'cmd': cmd,
                'output': result.stdout
            })
        except subprocess.CalledProcessError as e:
            return jsonify({
                'status': 'error',
                'cmd': cmd,
                'output': e.stdout,
                'error': e.stderr
            }), 400
    return jsonify({'error': 'no command supplied'}), 400

@APP.route('/', methods=['GET'])
def view_inventory():
    return jsonify(list_items())

@APP.route('/add', methods=['POST'])
def route_add():
    name = request.form.get('name')
    qty = request.form.get('qty')
    if not name or not qty:
        return jsonify({'error': 'missing parameters'}), 400
    try:
        qty = int(qty)
    except ValueError:
        return jsonify({'error': 'qty must be integer'}), 400
    item_id = add_item(name, qty)
    return jsonify({'status': 'added', 'id': item_id})

@APP.route('/update', methods=['POST'])
def route_update():
    item_id = request.form.get('id')
    qty = request.form.get('qty')
    if not item_id or not qty:
        return jsonify({'error': 'missing parameters'}), 400
    try:
        item_id = int(item_id)
        qty = int(qty)
    except ValueError:
        return jsonify({'error': 'id and qty must be integers'}), 400
    if update_item(item_id, qty):
        return jsonify({'status': 'updated', 'id': item_id})
    return jsonify({'error': 'item not found'}), 404

@APP.route('/run', methods=['GET'])
def route_run():
    return run_user_command()

if __name__ == '__main__':
    init_db()
    APP.run(host='127.0.0.1', port=5000)