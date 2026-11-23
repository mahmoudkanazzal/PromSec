import os
import logging
import bcrypt
import MySQLdb
import MySQLdb.cursors
from flask import Flask, request, jsonify, redirect, Response

logger = logging.getLogger('app')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

app = Flask(__name__)
app.config['DEBUG'] = False

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST,
                           user=DB_USER,
                           passwd=DB_PASSWORD,
                           db=DB_NAME,
                           charset='utf8',
                           cursorclass=MySQLdb.cursors.DictCursor)

def validate_field(value, name, min_len=1, max_len=255):
    if not isinstance(value, str):
        return f"{name} must be a string"
    if len(value) < min_len:
        return f"{name} must be at least {min_len} characters"
    if len(value) > max_len:
        return f"{name} must be at most {max_len} characters"
    return None

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        err = validate_field(username, 'username', 1, 150)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        err = validate_field(password, 'password', 8, 128)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        if password != confirm_password:
            return Response('Passwords do not match', status=400, mimetype='text/plain')
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return Response('Username already exists', status=400, mimetype='text/plain')
                cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
            conn.commit()
        return Response('You have successfully registered', status=200, mimetype='text/plain')
    except Exception:
        logger.error('Error during registration')
        return Response('Internal server error', status=500, mimetype='text/plain')

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        err = validate_field(username, 'username', 1, 150)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        err = validate_field(password, 'password', 1, 128)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
        if not row or not bcrypt.checkpw(password.encode('utf-8'), row['password_hash'].encode('utf-8')):
            return Response('Invalid credentials', status=401, mimetype='text/plain')
        return redirect('/dashboard')
    except Exception:
        logger.error('Error during login')
        return Response('Internal server error', status=500, mimetype='text/plain')

@app.route('/create_project', methods=['POST'])
def create_project():
    try:
        project_name = request.form.get('project_name', '')
        description = request.form.get('description', '')
        username = request.form.get('username', '')
        err = validate_field(project_name, 'project_name', 1, 150)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        err = validate_field(description, 'description', 0, 1000)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        err = validate_field(username, 'username', 1, 150)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if not cur.fetchone():
                    return Response('User does not exist', status=400, mimetype='text/plain')
                cur.execute("INSERT INTO projects (name, description, owner_username) VALUES (%s, %s, %s)", (project_name, description, username))
            conn.commit()
        return Response('Project created successfully', status=200, mimetype='text/plain')
    except Exception:
        logger.error('Error during project creation')
        return Response('Internal server error', status=500, mimetype='text/plain')

@app.route('/add_task', methods=['POST'])
def add_task():
    try:
        project_name = request.form.get('project_name', '')
        task_name = request.form.get('task_name', '')
        task_description = request.form.get('task_description', '')
        err = validate_field(project_name, 'project_name', 1, 150)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        err = validate_field(task_name, 'task_name', 1, 150)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        err = validate_field(task_description, 'task_description', 0, 1000)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM projects WHERE name = %s", (project_name,))
                if not cur.fetchone():
                    return Response('Project does not exist', status=400, mimetype='text/plain')
                cur.execute("INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)", (project_name, task_name, task_description))
            conn.commit()
        return Response('Task added successfully', status=200, mimetype='text/plain')
    except Exception:
        logger.error('Error during task addition')
        return Response('Internal server error', status=500, mimetype='text/plain')

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    try:
        project_name = request.args.get('project_name', '')
        err = validate_field(project_name, 'project_name', 1, 150)
        if err:
            return Response(err, status=400, mimetype='text/plain')
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT task_name, task_description FROM tasks WHERE project_name = %s", (project_name,))
                rows = cur.fetchall()
        return jsonify(rows), 200
    except Exception:
        logger.error('Error during viewing tasks')
        return Response('Internal server error', status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)