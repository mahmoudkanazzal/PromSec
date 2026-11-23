import os, hashlib
from flask import Flask, request, jsonify, redirect
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', 'projectdb'),
        charset='utf8mb4'
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing fields', 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
            if cur.fetchone():
                return redirect('/login', code=307)
            salt_bytes = os.urandom(16)
            salt_hex = salt_bytes.hex()
            pwd_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
            cur.execute(
                'INSERT INTO users (username, password_hash, salt, account_created) VALUES (%s, %s, %s, %s)',
                (username, pwd_hash, salt_hex, 1)
            )
            conn.commit()
            return 'Registration successful'
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing fields', 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT password_hash, salt FROM users WHERE username=%s', (username,))
            row = cur.fetchone()
            if not row:
                return 'Invalid credentials'
            stored_hash, salt_hex = row
            salt_bytes = bytes.fromhex(salt_hex)
            pwd_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
            if pwd_hash == stored_hash:
                return redirect('/dashboard', code=307)
            return 'Invalid credentials'
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/project/create', methods=['POST'])
def create_project():
    username = request.form.get('username')
    project_name = request.form.get('project_name')
    if not username or not project_name:
        return 'Missing fields', 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
            if not cur.fetchone():
                return 'User not found'
            cur.execute('INSERT INTO projects (username, project_name) VALUES (%s, %s)', (username, project_name))
            conn.commit()
            return 'Project created successfully'
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = request.form.get('project_name')
    task_name = request.form.get('task_name')
    task_description = request.form.get('task_description')
    if not project_name or not task_name or not task_description:
        return 'Missing fields', 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT 1 FROM projects WHERE project_name=%s', (project_name,))
            if not cur.fetchone():
                return 'Project not found'
            cur.execute(
                'INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)',
                (project_name, task_name, task_description)
            )
            conn.commit()
            return 'Task added successfully'
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify([])
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT task_name, task_description FROM tasks WHERE project_name=%s', (project_name,))
            rows = cur.fetchall()
            tasks = [{'task_name': r[0], 'task_description': r[1]} for r in rows]
            return jsonify(tasks)
        finally:
            cur.close()
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)