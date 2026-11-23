import os
import bcrypt
import MySQLdb
from flask import Flask, request, jsonify, redirect, url_for, make_response

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'appdb')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)

def query_one(cursor, query, params):
    cursor.execute(query, params)
    return cursor.fetchone()

def query_all(cursor, query, params):
    cursor.execute(query, params)
    return cursor.fetchall()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    password = data.get('password')
    confirm = data.get('confirm_password')
    if not username or not password or not confirm:
        return jsonify({'message': 'Missing fields'}), 400
    if password != confirm:
        return jsonify({'message': 'Passwords do not match'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if query_one(cur, "SELECT 1 FROM users WHERE username=%s", (username,)):
            return jsonify({'message': 'Username already exists'}), 409
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pw_hash))
        conn.commit()
        return jsonify({'message': 'User registered'}), 201
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return jsonify({'message': 'Database error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Missing fields'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        row = query_one(cur, "SELECT password_hash FROM users WHERE username=%s", (username,))
        if not row:
            return jsonify({'message': 'Invalid credentials'}), 401
        stored_hash = row[0].encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return jsonify({'message': 'Invalid credentials'}), 401
        return redirect(url_for('dashboard'))
    except MySQLdb.Error:
        return jsonify({'message': 'Database error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/dashboard')
def dashboard():
    return make_response('Dashboard', 200)

@app.route('/create_project', methods=['POST'])
def create_project():
    data = request.get_json(silent=True) or request.form
    project_name = data.get('project_name')
    username = data.get('username')
    description = data.get('description')
    if not project_name or not username:
        return jsonify({'message': 'Missing fields'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if not query_one(cur, "SELECT 1 FROM users WHERE username=%s", (username,)):
            return jsonify({'message': 'User does not exist'}), 404
        cur.execute("INSERT INTO projects (project_name, description, username) VALUES (%s, %s, %s)", (project_name, description, username))
        conn.commit()
        return jsonify({'message': 'Project created'}), 201
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return jsonify({'message': 'Database error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json(silent=True) or request.form
    project_name = data.get('project_name')
    task_name = data.get('task_name')
    task_description = data.get('task_description')
    if not project_name or not task_name:
        return jsonify({'message': 'Missing fields'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if not query_one(cur, "SELECT 1 FROM projects WHERE project_name=%s", (project_name,)):
            return jsonify({'message': 'Project does not exist'}), 404
        cur.execute("INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)", (project_name, task_name, task_description))
        conn.commit()
        return jsonify({'message': 'Task added'}), 201
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return jsonify({'message': 'Database error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify({'message': 'Missing project_name'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        rows = query_all(cur, "SELECT task_name, task_description FROM tasks WHERE project_name=%s", (project_name,))
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in rows]
        return jsonify(result), 200
    except MySQLdb.Error:
        return jsonify({'message': 'Database error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)