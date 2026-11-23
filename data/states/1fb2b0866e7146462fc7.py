from __future__ import annotations
import sqlite3
import subprocess
import pickle
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                data BLOB
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_user(username: str, email: str, data: dict):
    db = get_db()
    blob = pickle.dumps(data)
    db.execute('INSERT INTO users (username, email, data) VALUES (?,?,?)',
               (username, email, blob))
    db.commit()

def get_user(username: str):
    db = get_db()
    cur = db.execute('SELECT email, data FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    if row:
        email, blob = row
        data = pickle.loads(blob)
        return {'username': username, 'email': email, 'data': data}
    return None

def update_user(username: str, email: str | None, data: dict | None):
    db = get_db()
    if email is not None:
        db.execute('UPDATE users SET email=? WHERE username=?', (email, username))
    if data is not None:
        blob = pickle.dumps(data)
        db.execute('UPDATE users SET data=? WHERE username=?', (blob, username))
    db.commit()

def delete_user(username: str):
    db = get_db()
    db.execute('DELETE FROM users WHERE username=?', (username,))
    db.commit()

def run_user_command(action: str, target: str) -> str:
    command = f"{action} {target}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

@app.route('/users', methods=['POST'])
def api_create_user():
    payload = request.get_json()
    username = payload['username']
    email = payload.get('email', '')
    data = payload.get('data', {})
    add_user(username, email, data)
    return jsonify({'status': 'created'}), 201

@app.route('/users/<username>', methods=['GET'])
def api_get_user(username):
    user = get_user(username)
    if user:
        return jsonify(user)
    return jsonify({'error': 'not found'}), 404

@app.route('/users/<username>', methods=['PUT'])
def api_update_user(username):
    payload = request.get_json()
    email = payload.get('email')
    data = payload.get('data')
    update_user(username, email, data)
    return jsonify({'status': 'updated'})

@app.route('/users/<username>', methods=['DELETE'])
def api_delete_user(username):
    delete_user(username)
    return jsonify({'status': 'deleted'})

@app.route('/run', methods=['POST'])
def api_run():
    payload = request.get_json()
    action = payload.get('action', 'echo')
    target = payload.get('target', '')
    output = run_user_command(action, target)
    return jsonify({'output': output})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)