import os
import hashlib
from flask import Flask, request, redirect, jsonify
import MySQLdb
from contextlib import closing

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.secret_key = SECRET_KEY

def get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing fields', 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    return redirect('/login', code=307)
                salt_bytes = os.urandom(16)
                salt_hex = salt_bytes.hex()
                pwd_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
                cur.execute(
                    'INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, %s)',
                    (username, pwd_hash, salt_hex, 1)
                )
                conn.commit()
        return 'Registration successful'
    except Exception:
        return 'Internal server error', 500

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing fields', 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT password, salt FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
                if not row:
                    return 'Invalid credentials'
                stored_hash, stored_salt_hex = row
                salt_bytes = bytes.fromhex(stored_salt_hex)
                pwd_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
                if pwd_hash == stored_hash:
                    return redirect('/dashboard', code=307)
                else:
                    return 'Invalid credentials'
    except Exception:
        return 'Internal server error', 500

@app.route('/project/create', methods=['POST'])
def create_project():
    username = request.form.get('username')
    project_name = request.form.get('project_name')
    if not username or not project_name:
        return 'Missing fields', 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if not cur.fetchone():
                    return 'User not found'
                cur.execute(
                    'INSERT INTO projects (username, project_name) VALUES (%s, %s)',
                    (username, project_name)
                )
                conn.commit()
        return 'Project created successfully'
    except Exception:
        return 'Internal server error', 500

@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = request.form.get('project_name')
    task_name = request.form.get('task_name')
    task_description = request.form.get('task_description')
    if not project_name or not task_name or not task_description:
        return 'Missing fields', 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT 1 FROM projects WHERE project_name=%s', (project_name,))
                if not cur.fetchone():
                    return 'Project not found'
                cur.execute(
                    'INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)',
                    (project_name, task_name, task_description)
                )
                conn.commit()
        return 'Task added successfully'
    except Exception:
        return 'Internal server error', 500

@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name')
    if not project_name:
        return 'Missing project_name', 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'SELECT task_name, task_description FROM tasks WHERE project_name=%s',
                    (project_name,)
                )
                rows = cur.fetchall()
                tasks = [{'task_name': row[0], 'task_description': row[1]} for row in rows]
        return jsonify(tasks)
    except Exception:
        return 'Internal server error', 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)