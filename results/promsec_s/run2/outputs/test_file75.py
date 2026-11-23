import os
from flask import Flask, request, jsonify, redirect, url_for
import bcrypt
import MySQLdb
from contextlib import closing

app = Flask(__name__)

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

def get_connection():
    return MySQLdb.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DB,
        charset='utf8mb4',
        autocommit=False
    )

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')
    confirm = data.get('confirm_password')
    if not username or not password or not confirm:
        return jsonify({'error': 'Missing fields'}), 400
    if password != confirm:
        return jsonify({'error': 'Passwords do not match'}), 400
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT id FROM users WHERE username = %s', (username,))
                if cur.fetchone():
                    return jsonify({'error': 'Username already exists'}), 409
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, hashed))
                conn.commit()
        return jsonify({'message': 'User registered successfully'}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
                row = cur.fetchone()
                if not row:
                    return jsonify({'error': 'Invalid credentials'}), 401
                stored_hash = row[0].encode('utf-8')
                if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return jsonify({'error': 'Invalid credentials'}), 401
        return redirect(url_for('dashboard'))
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard')
def dashboard():
    return jsonify({'message': 'Welcome to the dashboard'}), 200

@app.route('/create_project', methods=['POST'])
def create_project():
    data = request.get_json() or request.form
    project_name = data.get('project_name')
    description = data.get('description')
    username = data.get('username')
    if not project_name or not description or not username:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT id FROM users WHERE username = %s', (username,))
                user = cur.fetchone()
                if not user:
                    return jsonify({'error': 'User not found'}), 400
                user_id = user[0]
                cur.execute('SELECT id FROM projects WHERE name = %s AND user_id = %s', (project_name, user_id))
                if cur.fetchone():
                    return jsonify({'error': 'Project already exists'}), 409
                cur.execute('INSERT INTO projects (user_id, name, description) VALUES (%s, %s, %s)', (user_id, project_name, description))
                conn.commit()
        return jsonify({'message': 'Project created successfully'}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json() or request.form
    project_name = data.get('project_name')
    task_name = data.get('task_name')
    task_description = data.get('task_description')
    if not project_name or not task_name or not task_description:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT id FROM projects WHERE name = %s', (project_name,))
                project = cur.fetchone()
                if not project:
                    return jsonify({'error': 'Project not found'}), 400
                project_id = project[0]
                cur.execute('INSERT INTO tasks (project_id, name, description) VALUES (%s, %s, %s)', (project_id, task_name, task_description))
                conn.commit()
        return jsonify({'message': 'Task added successfully'}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify({'error': 'Missing project_name parameter'}), 400
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor(MySQLdb.cursors.DictCursor)) as cur:
                cur.execute('SELECT id FROM projects WHERE name = %s', (project_name,))
                project = cur.fetchone()
                if not project:
                    return jsonify({'error': 'Project not found'}), 400
                project_id = project['id']
                cur.execute('SELECT name, description FROM tasks WHERE project_id = %s', (project_id,))
                tasks = cur.fetchall()
        return jsonify({'tasks': tasks}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False)