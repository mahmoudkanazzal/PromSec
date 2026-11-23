import os
import json
import bcrypt
import MySQLdb
from flask import Flask, request, abort, jsonify, redirect, url_for

app = Flask(__name__)

def get_db_connection():
    """Create and return a MySQLdb connection using environment variables."""
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'appdb')
    try:
        conn = MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=db,
            charset='utf8mb4',
            use_unicode=True,
            autocommit=False
        )
        return conn
    except MySQLdb.Error as e:
        raise RuntimeError(f'Database connection error: {e}')

@app.route('/register', methods=['POST'])
def register():
    """Register a new user with a hashed password."""
    username = request.form.get('username')
    password = request.form.get('password')
    confirm = request.form.get('confirm_password')
    if not username or not password or not confirm:
        abort(400, description='Missing required fields')
    if password != confirm:
        abort(400, description='Passwords do not match')
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            abort(409, description='Username already exists')
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
            (username, password_hash)
        )
        conn.commit()
        return jsonify(message='User registered successfully'), 201
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    """Authenticate a user and redirect to the dashboard on success."""
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Missing username or password')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if not row:
            abort(401, description='Invalid credentials')
        stored_hash = row[0].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return redirect(url_for('dashboard'))
        else:
            abort(401, description='Invalid credentials')
    except MySQLdb.Error as e:
        return jsonify(error=str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Placeholder dashboard indicating successful login."""
    return 'Welcome to your dashboard', 200

@app.route('/create_project', methods=['POST'])
def create_project():
    """Create a new project associated with an existing user."""
    project_name = request.form.get('project_name')
    description = request.form.get('description')
    username = request.form.get('username')
    if not project_name or not description or not username:
        abort(400, description='Missing required fields')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if not cursor.fetchone():
            abort(404, description='User not found')
        cursor.execute(
            'INSERT INTO projects (project_name, description, username) VALUES (%s, %s, %s)',
            (project_name, description, username)
        )
        conn.commit()
        return jsonify(message='Project created successfully'), 201
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/add_task', methods=['POST'])
def add_task():
    """Add a new task to an existing project."""
    project_name = request.form.get('project_name')
    task_name = request.form.get('task_name')
    task_description = request.form.get('task_description')
    if not project_name or not task_name or not task_description:
        abort(400, description='Missing required fields')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM projects WHERE project_name = %s', (project_name,))
        if not cursor.fetchone():
            abort(404, description='Project not found')
        cursor.execute(
            'INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)',
            (project_name, task_name, task_description)
        )
        conn.commit()
        return jsonify(message='Task added successfully'), 201
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    """Return all tasks for a given project as JSON."""
    project_name = request.args.get('project_name')
    if not project_name:
        abort(400, description='Missing project_name parameter')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT task_name, task_description FROM tasks WHERE project_name = %s',
            (project_name,)
        )
        rows = cursor.fetchall()
        tasks = [{'task_name': row[0], 'task_description': row[1]} for row in rows]
        return jsonify(tasks), 200
    except MySQLdb.Error as e:
        return jsonify(error=str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)