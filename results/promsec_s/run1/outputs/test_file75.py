import os
import re
import bcrypt
import mysql.connector
from flask import Flask, request, redirect, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config['DEBUG'] = False
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

username_regex = re.compile(r'^[A-Za-z0-9]{3,30}$')
name_regex = re.compile(r'^[A-Za-z0-9 ]{1,100}$')
password_regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')

def valid_username(u):
    return bool(username_regex.fullmatch(u))

def valid_name(n):
    return bool(name_regex.fullmatch(n))

def valid_password(p):
    return bool(password_regex.fullmatch(p))

@app.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not (valid_username(username) and valid_password(password) and password == confirm_password):
            return 'Registration Failed', 400
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return 'Username already exists', 409
                cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
                conn.commit()
        return 'You have successfully registered', 201
    except Exception:
        return 'Registration Failed', 500

@app.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            return 'Invalid credentials', 401
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                if not row:
                    return 'Invalid credentials', 401
                stored_hash = row[0]
                if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    return redirect('/dashboard')
                else:
                    return 'Invalid credentials', 401
    except Exception:
        return 'Invalid credentials', 401

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return 'Welcome to the dashboard', 200

@app.route('/create_project', methods=['POST'])
@limiter.limit("5 per minute")
def create_project():
    try:
        project_name = request.form.get('project_name', '').strip()
        description = request.form.get('description', '').strip()
        username = request.form.get('username', '').strip()
        if not (valid_name(project_name) and valid_username(username)):
            return 'Project creation failed', 400
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if not cur.fetchone():
                    return 'User does not exist', 404
                cur.execute(
                    "INSERT INTO projects (project_name, description, username) VALUES (%s, %s, %s)",
                    (project_name, description, username)
                )
                conn.commit()
        return 'Project created successfully', 201
    except Exception:
        return 'Project creation failed', 500

@app.route('/add_task', methods=['POST'])
@limiter.limit("10 per minute")
def add_task():
    try:
        project_name = request.form.get('project_name', '').strip()
        task_name = request.form.get('task_name', '').strip()
        task_description = request.form.get('task_description', '').strip()
        if not (valid_name(project_name) and valid_name(task_name)):
            return 'Task addition failed', 400
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM projects WHERE project_name = %s", (project_name,))
                if not cur.fetchone():
                    return 'Project does not exist', 404
                cur.execute(
                    "INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)",
                    (project_name, task_name, task_description)
                )
                conn.commit()
        return 'Task added successfully', 201
    except Exception:
        return 'Task addition failed', 500

@app.route('/view_tasks', methods=['GET'])
@limiter.limit("20 per minute")
def view_tasks():
    try:
        project_name = request.args.get('project_name', '').strip()
        if not valid_name(project_name):
            return jsonify({'error': 'Invalid project name'}), 400
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT task_name, task_description FROM tasks WHERE project_name = %s",
                    (project_name,)
                )
                tasks = cur.fetchall()
        return jsonify(tasks), 200
    except Exception:
        return jsonify({'error': 'Failed to retrieve tasks'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)