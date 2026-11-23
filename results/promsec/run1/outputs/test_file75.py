import os, re, contextlib
import MySQLdb
import bcrypt
from flask import Flask, request, redirect, jsonify, make_response

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_]{3,20}$')
PROJECT_REGEX = re.compile(r'^[A-Za-z0-9_ ]{3,50}$')
TASK_REGEX = re.compile(r'^[A-Za-z0-9_ ]{1,100}$')

def get_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')

def validate_username(username):
    return USERNAME_REGEX.fullmatch(username) is not None

def validate_project_name(name):
    return PROJECT_REGEX.fullmatch(name) is not None

def validate_task_name(name):
    return TASK_REGEX.fullmatch(name) is not None

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    if not (username and password and confirm):
        return make_response('Missing fields', 400, {'Content-Type':'text/plain'})
    if not validate_username(username):
        return make_response('Invalid username', 400, {'Content-Type':'text/plain'})
    if password != confirm:
        return make_response('Passwords do not match', 400, {'Content-Type':'text/plain'})
    pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        with contextlib.closing(get_connection()) as conn:
            with contextlib.closing(conn.cursor()) as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    return make_response('Username already exists', 400, {'Content-Type':'text/plain'})
                cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
                conn.commit()
        return make_response('Registration successful', 200, {'Content-Type':'text/plain'})
    except MySQLdb.Error:
        return make_response('Database error', 500, {'Content-Type':'text/plain'})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not (username and password):
        return make_response('Missing fields', 400, {'Content-Type':'text/plain'})
    try:
        with contextlib.closing(get_connection()) as conn:
            with contextlib.closing(conn.cursor()) as cur:
                cur.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
                if not row:
                    return make_response('Invalid credentials', 401, {'Content-Type':'text/plain'})
                stored_hash = row[0].encode('utf-8')
                if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return make_response('Invalid credentials', 401, {'Content-Type':'text/plain'})
        return redirect('/dashboard')
    except MySQLdb.Error:
        return make_response('Database error', 500, {'Content-Type':'text/plain'})

@app.route('/create_project', methods=['POST'])
def create_project():
    project_name = request.form.get('project_name', '').strip()
    description = request.form.get('description', '').strip()
    username = request.form.get('username', '').strip()
    if not (project_name and description and username):
        return make_response('Missing fields', 400, {'Content-Type':'text/plain'})
    if not validate_project_name(project_name):
        return make_response('Invalid project name', 400, {'Content-Type':'text/plain'})
    try:
        with contextlib.closing(get_connection()) as conn:
            with contextlib.closing(conn.cursor()) as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if not cur.fetchone():
                    return make_response('User does not exist', 400, {'Content-Type':'text/plain'})
                cur.execute('INSERT INTO projects (project_name, description, owner_username) VALUES (%s, %s, %s)', (project_name, description, username))
                conn.commit()
        return make_response('Project created', 200, {'Content-Type':'text/plain'})
    except MySQLdb.Error:
        return make_response('Database error', 500, {'Content-Type':'text/plain'})

@app.route('/add_task', methods=['POST'])
def add_task():
    project_name = request.form.get('project_name', '').strip()
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    if not (project_name and task_name and task_description):
        return make_response('Missing fields', 400, {'Content-Type':'text/plain'})
    if not validate_project_name(project_name) or not validate_task_name(task_name):
        return make_response('Invalid input', 400, {'Content-Type':'text/plain'})
    try:
        with contextlib.closing(get_connection()) as conn:
            with contextlib.closing(conn.cursor()) as cur:
                cur.execute('SELECT 1 FROM projects WHERE project_name=%s', (project_name,))
                if not cur.fetchone():
                    return make_response('Project does not exist', 400, {'Content-Type':'text/plain'})
                cur.execute('INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)', (project_name, task_name, task_description))
                conn.commit()
        return make_response('Task added', 200, {'Content-Type':'text/plain'})
    except MySQLdb.Error:
        return make_response('Database error', 500, {'Content-Type':'text/plain'})

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name', '').strip()
    if not project_name:
        return make_response('Missing project_name', 400, {'Content-Type':'text/plain'})
    if not validate_project_name(project_name):
        return make_response('Invalid project name', 400, {'Content-Type':'text/plain'})
    try:
        with contextlib.closing(get_connection()) as conn:
            with contextlib.closing(conn.cursor(MySQLdb.cursors.DictCursor)) as cur:
                cur.execute('SELECT task_name, task_description FROM tasks WHERE project_name=%s', (project_name,))
                tasks = cur.fetchall()
        return jsonify(tasks)
    except MySQLdb.Error:
        return make_response('Database error', 500, {'Content-Type':'text/plain'})

if __name__ == '__main__':
    app.run(debug=False)