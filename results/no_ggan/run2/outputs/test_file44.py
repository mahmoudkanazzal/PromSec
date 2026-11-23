import os
from flask import Flask, request, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'test')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST,
                           user=DB_USER,
                           passwd=DB_PASSWORD,
                           db=DB_NAME,
                           charset='utf8mb4',
                           use_unicode=True)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Username and password required', 400
    hashed = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return 'Username already exists', 409
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, hashed))
        conn.commit()
        return redirect('/home')
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Username and password required', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if not row or not check_password_hash(row[0], password):
            return 'Invalid credentials', 401
        return redirect('/dashboard')
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/add_task', methods=['POST'])
def add_task():
    username = request.form.get('username')
    task_name = request.form.get('task_name')
    task_description = request.form.get('task_description')
    if not username or not task_name:
        return 'Username and task name required', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if not cursor.fetchone():
            return 'User not found', 404
        cursor.execute('INSERT INTO tasks (username, task_name, task_description) VALUES (%s, %s, %s)', (username, task_name, task_description))
        conn.commit()
        return 'Task added successfully', 201
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    username = request.args.get('username')
    if not username:
        return 'Username required', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT task_id, task_name, task_description FROM tasks WHERE username = %s', (username,))
        tasks = cursor.fetchall()
        return jsonify(tasks), 200
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_task', methods=['POST'])
def delete_task():
    username = request.form.get('username')
    task_id = request.form.get('task_id')
    if not username or not task_id:
        return 'Username and task ID required', 400
    try:
        task_id_int = int(task_id)
    except ValueError:
        return 'Invalid task ID', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE username = %s AND task_id = %s', (username, task_id_int))
        if cursor.rowcount == 0:
            return 'Task not found', 404
        conn.commit()
        return 'Task deleted successfully', 200
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/update_task', methods=['POST'])
def update_task():
    username = request.form.get('username')
    task_id = request.form.get('task_id')
    new_task_name = request.form.get('new_task_name')
    new_task_description = request.form.get('new_task_description')
    if not username or not task_id or not new_task_name:
        return 'Username, task ID, and new task name required', 400
    try:
        task_id_int = int(task_id)
    except ValueError:
        return 'Invalid task ID', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET task_name = %s, task_description = %s WHERE username = %s AND task_id = %s', (new_task_name, new_task_description, username, task_id_int))
        if cursor.rowcount == 0:
            return 'Task not found', 404
        conn.commit()
        return 'Task updated successfully', 200
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)