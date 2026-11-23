from __future__ import annotations
import sqlite3
import hashlib
from flask import Flask, request, jsonify, g

DATABASE = 'users.db'
app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT
        )''')
        conn.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    pwd = data.get('password')
    if not username or not pwd:
        return jsonify({'error': 'username and password required'}), 400
    pw_hash = hash_password(pwd)
    db = get_db()
    try:
        db.execute('INSERT INTO users (username, email, password_hash) VALUES (?,?,?)',
                   (username, email, pw_hash))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'username already exists'}), 409
    return jsonify({'message': 'user created'}), 201

@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    db = get_db()
    cur = db.execute('SELECT username, email FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    if row is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify(dict(row))

@app.route('/users/<username>', methods=['PUT'])
def update_user(username):
    data = request.get_json()
    email = data.get('email')
    pwd = data.get('password')
    db = get_db()
    if email is not None and pwd is not None:
        db.execute(
            'UPDATE users SET email=?, password_hash=? WHERE username=?',
            (email, hash_password(pwd), username)
        )
    elif email is not None:
        db.execute(
            'UPDATE users SET email=? WHERE username=?',
            (email, username)
        )
    elif pwd is not None:
        db.execute(
            'UPDATE users SET password_hash=? WHERE username=?',
            (hash_password(pwd), username)
        )
    else:
        return jsonify({'error': 'nothing to update'}), 400
    db.commit()
    return jsonify({'message': 'updated'})

@app.route('/users/<username>', methods=['DELETE'])
def delete_user(username):
    db = get_db()
    cur = db.execute('DELETE FROM users WHERE username=?', (username,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'message': 'deleted'})

@app.route('/users', methods=['GET'])
def list_users():
    db = get_db()
    cur = db.execute('SELECT username, email FROM users')
    users = [dict(row) for row in cur.fetchall()]
    return jsonify(users)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)