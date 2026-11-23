import os
import re
import MySQLdb
import MySQLdb.cursors
from flask import Flask, request, abort, redirect, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super-secret-key')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'appdb')

USERNAME_REGEX = re.compile(r'^\w{3,30}$')


def get_db_connection():
    conn = MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True,
        cursorclass=MySQLdb.cursors.DictCursor,
    )
    conn.autocommit(False)
    return conn


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        abort(400, description='Username and password are required')
    if not USERNAME_REGEX.match(username):
        abort(400, description='Invalid username format')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
            (username, password_hash)
        )
        conn.commit()
        return make_response('User registered successfully', 200)
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        abort(500, description='Internal server error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        abort(400, description='Username and password are required')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row['password_hash'], password):
            return redirect('/dashboard', code=307)
        else:
            return make_response('Invalid credentials', 401)
    except MySQLdb.Error:
        abort(500, description='Internal server error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/project/create', methods=['POST'])
def create_project():
    username = request.form.get('username', '').strip()
    project_name = request.form.get('project_name', '').strip()
    if not username or not project_name:
        abort(400, description='Username and project name are required')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if not cursor.fetchone():
            return make_response('User not found', 404)
        cursor.execute(
            'INSERT INTO projects (username, project_name) VALUES (%s, %s)',
            (username, project_name)
        )
        conn.commit()
        return make_response('Project created successfully', 200)
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        abort(500, description='Internal server error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = request.form.get('project_name', '').strip()
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    if not project_name or not task_name:
        abort(400, description='Project name and task name are required')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM projects WHERE project_name = %s', (project_name,))
        if not cursor.fetchone():
            return make_response('Project not found', 404)
        cursor.execute(
            'INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)',
            (project_name, task_name, task_description)
        )
        conn.commit()
        return make_response('Task added successfully', 200)
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        abort(500, description='Internal server error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name', '').strip()
    if not project_name:
        abort(400, description='project_name query parameter is required')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT task_name, task_description FROM tasks WHERE project_name = %s',
            (project_name,)
        )
        tasks = cursor.fetchall()
        return jsonify(tasks)
    except MySQLdb.Error:
        abort(500, description='Internal server error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/dashboard', methods=['GET'])
def dashboard():
    return make_response('Dashboard placeholder - login successful', 200)


@app.errorhandler(500)
def internal_error(error):
    return make_response('Internal server error', 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)