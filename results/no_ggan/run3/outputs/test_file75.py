import os
import bcrypt
import MySQLdb
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'project_manager')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            return jsonify({'message': 'Username already exists'}), 409
        cur.execute('INSERT INTO users (username, pw_hash) VALUES (%s, %s)', (username, pw_hash.decode('utf-8')))
        conn.commit()
        return jsonify({'message': 'You have successfully registered'}), 201
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return jsonify({'message': 'Registration Failed'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT pw_hash FROM users WHERE username = %s', (username,))
        row = cur.fetchone()
    except MySQLdb.Error:
        return jsonify({'message': 'Login Failed'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    if row and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
        return redirect('/dashboard')
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/create_project', methods=['POST'])
def create_project():
    project_name = request.form.get('project_name', '').strip()
    description = request.form.get('description', '').strip()
    username = request.form.get('username', '').strip()
    if not project_name or not username:
        return jsonify({'message': 'Project name and username are required'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if not cur.fetchone():
            return jsonify({'message': 'User not found'}), 404
        cur.execute('INSERT INTO projects (project_name, description, username) VALUES (%s, %s, %s)', (project_name, description, username))
        conn.commit()
        return jsonify({'message': 'Project created successfully'}), 201
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return jsonify({'message': 'Project creation failed'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/add_task', methods=['POST'])
def add_task():
    project_name = request.form.get('project_name', '').strip()
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    if not project_name or not task_name:
        return jsonify({'message': 'Project name and task name are required'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM projects WHERE project_name = %s', (project_name,))
        if not cur.fetchone():
            return jsonify({'message': 'Project not found'}), 404
        cur.execute('INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)', (project_name, task_name, task_description))
        conn.commit()
        return jsonify({'message': 'Task added successfully'}), 201
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return jsonify({'message': 'Task addition failed'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name', '').strip()
    if not project_name:
        return jsonify({'message': 'Project name is required'}), 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM tasks WHERE project_name = %s', (project_name,))
        rows = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return jsonify(result), 200
    except MySQLdb.Error:
        return jsonify({'message': 'Failed to retrieve tasks'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)