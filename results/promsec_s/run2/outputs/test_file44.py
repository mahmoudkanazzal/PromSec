import os
import logging
from flask import Flask, request, jsonify, abort
from flask_wtf.csrf import CSRFProtect
import bcrypt
from mysql.connector import connect, Error
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
csrf = CSRFProtect(app)

def get_db_connection():
    return connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_field(data, field, max_len=None, min_len=None):
    if field not in data:
        return False
    value = data.get(field)
    if not isinstance(value, str):
        return False
    if max_len is not None and len(value) > max_len:
        return False
    if min_len is not None and len(value) < min_len:
        return False
    return True

@csrf.exempt
@app.route('/register', methods=['POST'])
def register():
    if not (validate_field(request.form, 'username', max_len=150) and validate_field(request.form, 'password', min_len=8)):
        return jsonify({'error': 'Invalid input'}), 400
    username = request.form['username']
    password = request.form['password']
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
                if cur.fetchone():
                    return jsonify({'error': 'Username already exists'}), 400
                pwd_hash = hash_password(password)
                cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
                conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except Error as e:
        logging.error(e)
        return jsonify({'error': 'Server error'}), 500

@csrf.exempt
@app.route('/login', methods=['POST'])
def login():
    if not (validate_field(request.form, 'username') and validate_field(request.form, 'password')):
        return jsonify({'error': 'Invalid input'}), 400
    username = request.form['username']
    password = request.form['password']
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
                row = cur.fetchone()
                if not row or not check_password(password, row[0]):
                    return jsonify({'error': 'Invalid credentials'}), 401
        return jsonify({'message': 'Login successful'}), 200
    except Error as e:
        logging.error(e)
        return jsonify({'error': 'Server error'}), 500

@app.route('/add_task', methods=['POST'])
def add_task():
    required = ['username', 'task_name', 'task_description']
    for field in required:
        if field not in request.form:
            return jsonify({'error': 'Invalid input'}), 400
    username = request.form['username']
    task_name = request.form['task_name']
    task_description = request.form['task_description']
    if not (validate_field(request.form, 'username') and validate_field(request.form, 'task_name', max_len=200) and validate_field(request.form, 'task_description', max_len=500)):
        return jsonify({'error': 'Invalid input'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
                if not cur.fetchone():
                    return jsonify({'error': 'User not found'}), 404
                cur.execute('INSERT INTO tasks (username, task_name, task_description) VALUES (%s, %s, %s)', (username, task_name, task_description))
                conn.commit()
        return jsonify({'message': 'Task successfully added'}), 201
    except Error as e:
        logging.error(e)
        return jsonify({'error': 'Server error'}), 500

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute('SELECT id, task_name, task_description FROM tasks WHERE username = %s', (username,))
                tasks = cur.fetchall()
        return jsonify({'tasks': tasks}), 200
    except Error as e:
        logging.error(e)
        return jsonify({'error': 'Server error'}), 500

@app.route('/delete_task', methods=['POST'])
def delete_task():
    if not (validate_field(request.form, 'username') and validate_field(request.form, 'task_id')):
        return jsonify({'error': 'Invalid input'}), 400
    username = request.form['username']
    try:
        task_id = int(request.form['task_id'])
    except ValueError:
        return jsonify({'error': 'Invalid task_id'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM tasks WHERE id = %s AND username = %s', (task_id, username))
                if cur.rowcount == 0:
                    return jsonify({'error': 'Task not found'}), 404
                conn.commit()
        return jsonify({'message': 'Task successfully deleted'}), 200
    except Error as e:
        logging.error(e)
        return jsonify({'error': 'Server error'}), 500

@app.route('/update_task', methods=['POST'])
def update_task():
    required = ['username', 'task_id', 'new_task_name', 'new_task_description']
    for field in required:
        if field not in request.form:
            return jsonify({'error': 'Invalid input'}), 400
    username = request.form['username']
    if not (validate_field(request.form, 'new_task_name', max_len=200) and validate_field(request.form, 'new_task_description', max_len=500)):
        return jsonify({'error': 'Invalid input'}), 400
    try:
        task_id = int(request.form['task_id'])
    except ValueError:
        return jsonify({'error': 'Invalid task_id'}), 400
    new_name = request.form['new_task_name']
    new_desc = request.form['new_task_description']
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE tasks SET task_name = %s, task_description = %s WHERE id = %s AND username = %s', (new_name, new_desc, task_id, username))
                if cur.rowcount == 0:
                    return jsonify({'error': 'Task not found'}), 404
                conn.commit()
        return jsonify({'message': 'Task successfully updated'}), 200
    except Error as e:
        logging.error(e)
        return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)