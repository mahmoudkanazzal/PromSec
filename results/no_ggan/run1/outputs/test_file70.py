import os
import hashlib
from flask import Flask, request, redirect, jsonify, abort
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')

def get_db_connection():
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME, charset=DB_CHARSET, cursorclass=MySQLdb.cursors.DictCursor, autocommit=False)
    return conn

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex(), dk.hex()

def verify_password(stored_hash, stored_salt, password):
    salt_bytes = bytes.fromhex(stored_salt)
    _, computed_hash = hash_password(password, salt_bytes)
    return hashlib.compare_digest(stored_hash, computed_hash)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        abort(400)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cur.fetchone():
            return redirect('/login', code=307)
        salt_hex, hash_hex = hash_password(password)
        cur.execute('INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, NOW())', (username, hash_hex, salt_hex))
        conn.commit()
        return jsonify(message='User registered successfully')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        abort(400)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT password, salt FROM users WHERE username=%s', (username,))
        row = cur.fetchone()
        if not row or not verify_password(row['password'], row['salt'], password):
            abort(401, description='Invalid credentials')
        return redirect('/dashboard', code=307)
    finally:
        conn.close()

@app.route('/project/create', methods=['POST'])
def create_project():
    username = request.form.get('username', '').strip()
    project_name = request.form.get('project_name', '').strip()
    if not username or not project_name:
        abort(400)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if not cur.fetchone():
            abort(404, description='User not found')
        cur.execute('INSERT INTO projects (username, project_name) VALUES (%s, %s)', (username, project_name))
        conn.commit()
        return jsonify(message='Project created successfully')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = request.form.get('project_name', '').strip()
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    if not project_name or not task_name:
        abort(400)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM projects WHERE project_name=%s', (project_name,))
        if not cur.fetchone():
            abort(404, description='Project not found')
        cur.execute('INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)', (project_name, task_name, task_description))
        conn.commit()
        return jsonify(message='Task added successfully')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name', '').strip()
    if not project_name:
        abort(400)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT task_name, task_description FROM tasks WHERE project_name=%s', (project_name,))
        tasks = cur.fetchall()
        return jsonify(tasks)
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)