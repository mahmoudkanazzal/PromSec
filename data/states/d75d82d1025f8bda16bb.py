from __future__ import print_function

import sqlite3
import os
import shlex
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'inventory.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS items
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          name TEXT NOT NULL,
                          quantity INTEGER NOT NULL)''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_item(name, quantity):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO items (name, quantity) VALUES (?,?)',
                   (name, int(quantity)))
    db.commit()
    return cursor.lastrowid

def list_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, name, quantity FROM items')
    rows = cursor.fetchall()
    return [{'id': r[0], 'name': r[1], 'quantity': r[2]} for r in rows]

def run_report(command):
    import subprocess
    args = shlex.split(command)
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout + result.stderr

@app.route('/add', methods=['POST'])
def route_add():
    data = request.json
    if not data or 'name' not in data or 'quantity' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    item_id = add_item(data['name'], data['quantity'])
    return jsonify({'id': item_id}), 201

@app.route('/items', methods=['GET'])
def route_items():
    return jsonify(list_items())

@app.route('/report', methods=['GET'])
def route_report():
    cmd = request.args.get('cmd')
    if not cmd:
        return jsonify({'error': 'No command supplied'}), 400
    output = run_report(cmd)
    return jsonify({'output': output})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)