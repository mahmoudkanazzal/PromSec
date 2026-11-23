import os
import re
from flask import Flask, request, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'passwd': os.getenv('DB_PASS', ''),
    'db': os.getenv('DB_NAME', 'myapp'),
    'charset': 'utf8mb4',
    'cursorclass': MySQLdb.cursors.DictCursor
}

def get_db_connection():
    return MySQLdb.connect(**DB_CONFIG)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return 'Username and password are required', 400
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,30}$', username):
        return 'Invalid username format', 400
    password_hash = generate_password_hash(password)
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT username FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            return redirect('/login', code=307)
        cur.execute('INSERT INTO users (username, password, account_created) VALUES (%s, %s, NOW())', (username, password_hash))
        conn.commit()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return 'Registration successful', 200

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return 'Invalid credentials', 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username = %s', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row['password'], password):
            return redirect('/dashboard', code=307)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return 'Invalid credentials', 400

@app.route('/project/create', methods=['POST'])
def create_project():
    username = request.form.get('username', '').strip()
    project_name = request.form.get('project_name', '').strip()
    if not username or not project_name:
        return 'Missing parameters', 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT username FROM users WHERE username = %s', (username,))
        if not cur.fetchone():
            return 'User not found', 404
        cur.execute('INSERT INTO projects (username, project_name) VALUES (%s, %s)', (username, project_name))
        conn.commit()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return 'Project created successfully', 200

@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = request.form.get('project_name', '').strip()
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    if not project_name or not task_name:
        return 'Missing parameters', 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT project_name FROM projects WHERE project_name = %s', (project_name,))
        if not cur.fetchone():
            return 'Project not found', 404
        cur.execute('INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)', (project_name, task_name, task_description))
        conn.commit()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return 'Task added successfully', 200

@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name', '').strip()
    if not project_name:
        return 'Project name required', 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT task_name, task_description FROM tasks WHERE project_name = %s', (project_name,))
        tasks = cur.fetchall()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return jsonify(tasks), 200

if __name__ == '__main__':
    app.run(debug=False)