import os
import logging
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_wtf import CSRFProtect
from mysql.connector import Error, pooling
from werkzeug.security import generate_password_hash, check_password_hash

class Config:
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret')
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_SSL_CA = os.getenv('DB_SSL_CA')
    DB_SSL_CERT = os.getenv('DB_SSL_CERT')
    DB_SSL_KEY = os.getenv('DB_SSL_KEY')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_db_pool = None

def _create_db_pool():
    cfg = {
        'host': Config.DB_HOST,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
        'pool_name': 'mypool',
        'pool_size': 5,
    }
    if Config.DB_SSL_CA:
        cfg['ssl_ca'] = Config.DB_SSL_CA
    if Config.DB_SSL_CERT:
        cfg['ssl_cert'] = Config.DB_SSL_CERT
    if Config.DB_SSL_KEY:
        cfg['ssl_key'] = Config.DB_SSL_KEY
    return pooling.MySQLConnectionPool(**cfg)

def get_connection():
    global _db_pool
    if _db_pool is None:
        _db_pool = _create_db_pool()
    return _db_pool.get_connection()

def validate_string(value, field_name, max_length=255):
    if not isinstance(value, str):
        return f'{field_name} must be a string'
    trimmed = value.strip()
    if not trimmed:
        return f'{field_name} cannot be empty'
    if len(trimmed) > max_length:
        return f'{field_name} exceeds maximum length of {max_length}'
    return None

def get_user_by_username(username):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, username, password FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        return result
    except Error as e:
        logger.error(f'Database error in get_user_by_username: {e}')
        raise
    finally:
        cursor.close()
        conn.close()

def create_user(username, password_hash):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(query, (username, password_hash))
        conn.commit()
    except Error as e:
        logger.error(f'Database error in create_user: {e}')
        raise
    finally:
        cursor.close()
        conn.close()

def add_task(username, title, description):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO tasks (username, title, description) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, title, description))
        conn.commit()
    except Error as e:
        logger.error(f'Database error in add_task: {e}')
        raise
    finally:
        cursor.close()
        conn.close()

def get_tasks(username):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, title, description FROM tasks WHERE username = %s"
        cursor.execute(query, (username,))
        return cursor.fetchall()
    except Error as e:
        logger.error(f'Database error in get_tasks: {e}')
        raise
    finally:
        cursor.close()
        conn.close()

def update_task(username, task_id, title, description):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "UPDATE tasks SET title = %s, description = %s WHERE username = %s AND id = %s"
        cursor.execute(query, (title, description, username, task_id))
        conn.commit()
        return cursor.rowcount
    except Error as e:
        logger.error(f'Database error in update_task: {e}')
        raise
    finally:
        cursor.close()
        conn.close()

def delete_task(username, task_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "DELETE FROM tasks WHERE username = %s AND id = %s"
        cursor.execute(query, (username, task_id))
        conn.commit()
        return cursor.rowcount
    except Error as e:
        logger.error(f'Database error in delete_task: {e}')
        raise
    finally:
        cursor.close()
        conn.close()

@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return jsonify(error='Authentication required'), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify(error='Invalid JSON'), 400
    username = data.get('username')
    password = data.get('password')
    err = validate_string(username, 'username')
    if err:
        return jsonify(error=err), 400
    err = validate_string(password, 'password')
    if err:
        return jsonify(error=err), 400
    if get_user_by_username(username):
        return jsonify(error='Username already exists'), 409
    password_hash = generate_password_hash(password)
    try:
        create_user(username, password_hash)
    except Exception:
        return jsonify(error='User creation failed'), 500
    session['username'] = username
    return redirect(url_for('list_tasks'))

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify(error='Invalid JSON'), 400
    username = data.get('username')
    password = data.get('password')
    err = validate_string(username, 'username')
    if err:
        return jsonify(error=err), 400
    err = validate_string(password, 'password')
    if err:
        return jsonify(error=err), 400
    user = get_user_by_username(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify(error='Invalid credentials'), 401
    session['username'] = username
    return redirect(url_for('list_tasks'))

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify(message='Logged out'), 200

@app.route('/tasks', methods=['GET'])
@login_required
def list_tasks():
    username = session['username']
    tasks = get_tasks(username)
    return jsonify(tasks=tasks), 200

@app.route('/tasks', methods=['POST'])
@csrf.exempt
@login_required
def create_task():
    data = request.get_json()
    if not data:
        return jsonify(error='Invalid JSON'), 400
    title = data.get('title')
    description = data.get('description', '')
    err = validate_string(title, 'title', 255)
    if err:
        return jsonify(error=err), 400
    if description is not None:
        err = validate_string(description, 'description', 1024)
        if err:
            return jsonify(error=err), 400
    else:
        description = ''
    try:
        add_task(session['username'], title.strip(), description.strip())
    except Exception:
        return jsonify(error='Task creation failed'), 500
    return jsonify(message='Task added'), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
@csrf.exempt
@login_required
def modify_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify(error='Invalid JSON'), 400
    title = data.get('title')
    description = data.get('description', '')
    err = validate_string(title, 'title', 255)
    if err:
        return jsonify(error=err), 400
    if description is not None:
        err = validate_string(description, 'description', 1024)
        if err:
            return jsonify(error=err), 400
    else:
        description = ''
    try:
        rows = update_task(session['username'], task_id, title.strip(), description.strip())
    except Exception:
        return jsonify(error='Task update failed'), 500
    if rows == 0:
        return jsonify(error='Task not found'), 404
    return jsonify(message='Task updated'), 200

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def remove_task(task_id):
    try:
        rows = delete_task(session['username'], task_id)
    except Exception:
        return jsonify(error='Task deletion failed'), 500
    if rows == 0:
        return jsonify(error='Task not found'), 404
    return jsonify(message='Task deleted'), 200

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=host, port=port, debug=False)