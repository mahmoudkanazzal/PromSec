import os
from flask import Flask, request, redirect, jsonify, make_response
import MySQLdb
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def get_db():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        cursorclass=MySQLdb.cursors.DictCursor
    )

def validate_field(data, field, max_len=150):
    value = data.get(field)
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or len(cleaned) > max_len:
        return None
    return cleaned

@app.route('/register', methods=['POST'])
def register():
    username = validate_field(request.form, 'username')
    password = validate_field(request.form, 'password')
    if not username or not password:
        return make_response('Bad request', 400)
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    return redirect('/login', code=307)
                salt = os.urandom(16).hex()
                pwd_hash = generate_password_hash(password + salt, method='pbkdf2:sha256')
                cur.execute(
                    'INSERT INTO users (username, password_hash, salt, account_created) VALUES (%s, %s, %s, %s)',
                    (username, pwd_hash, salt, True)
                )
            conn.commit()
        return make_response('Registration successful', 200)
    except MySQLdb.Error:
        return make_response('Internal server error', 500)

@app.route('/login', methods=['POST'])
def login():
    username = validate_field(request.form, 'username')
    password = validate_field(request.form, 'password')
    if not username or not password:
        return make_response('Bad request', 400)
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT password_hash, salt FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
                if not row:
                    resp = make_response('Invalid credentials', 401)
                    resp.headers['Content-Type'] = 'text/plain'
                    return resp
                pwd_hash = row['password_hash']
                salt = row['salt']
                if check_password_hash(pwd_hash, password + salt):
                    return redirect('/dashboard', code=307)
                else:
                    resp = make_response('Invalid credentials', 401)
                    resp.headers['Content-Type'] = 'text/plain'
                    return resp
    except MySQLdb.Error:
        return make_response('Internal server error', 500)

@app.route('/project/create', methods=['POST'])
def create_project():
    username = validate_field(request.form, 'username')
    project_name = validate_field(request.form, 'project_name')
    if not username or not project_name:
        return make_response('Bad request', 400)
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if not cur.fetchone():
                    return make_response('User not found', 404)
                cur.execute('INSERT INTO projects (username, project_name) VALUES (%s, %s)', (username, project_name))
            conn.commit()
        return make_response('Project created', 200)
    except MySQLdb.Error:
        return make_response('Internal server error', 500)

@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = validate_field(request.form, 'project_name')
    task_name = validate_field(request.form, 'task_name')
    raw_desc = request.form.get('task_description')
    if raw_desc is None:
        return make_response('Bad request', 400)
    task_description = raw_desc.strip()
    if len(task_description) > 500:
        return make_response('Bad request', 400)
    if not project_name or not task_name:
        return make_response('Bad request', 400)
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM projects WHERE project_name=%s', (project_name,))
                if not cur.fetchone():
                    return make_response('Project not found', 404)
                cur.execute(
                    'INSERT INTO tasks (project_name, task_name, task_description) VALUES (%s, %s, %s)',
                    (project_name, task_name, task_description)
                )
            conn.commit()
        return make_response('Task added', 200)
    except MySQLdb.Error:
        return make_response('Internal server error', 500)

@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name', '')
    project_name = project_name.strip()
    if not project_name:
        return make_response('Bad request', 400)
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT task_name, task_description FROM tasks WHERE project_name=%s', (project_name,))
                rows = cur.fetchall()
        return jsonify(rows)
    except MySQLdb.Error:
        return make_response('Internal server error', 500)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)