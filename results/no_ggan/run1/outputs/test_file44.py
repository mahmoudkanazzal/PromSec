import os
import MySQLdb
from flask import Flask, request, redirect, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'task_manager')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 409
        pw_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pw_hash))
        conn.commit()
        return redirect('/home')
    except MySQLdb.Error as e:
        app.logger.error(f"Database error in register: {e}")
        return jsonify({'error': 'Internal server error'}), 500
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
        return jsonify({'error': 'Missing username or password'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
        row = cursor.fetchone()
        if not row or not check_password_hash(row[0], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        return redirect('/dashboard')
    except MySQLdb.Error as e:
        app.logger.error(f"Database error in login: {e}")
        return jsonify({'error': 'Internal server error'}), 500
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
        return jsonify({'error': 'Missing username or task_name'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        if not cursor.fetchone():
            return jsonify({'error': 'User not found'}), 404
        cursor.execute(
            "INSERT INTO tasks (username, task_name, task_description) VALUES (%s, %s, %s)",
            (username, task_name, task_description)
        )
        conn.commit()
        return jsonify({'message': 'Task added'}), 201
    except MySQLdb.Error as e:
        app.logger.error(f"Database error in add_task: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Missing username'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT task_id, task_name, task_description FROM tasks WHERE username=%s",
            (username,)
        )
        tasks = cursor.fetchall()
        return jsonify(tasks), 200
    except MySQLdb.Error as e:
        app.logger.error(f"Database error in view_tasks: {e}")
        return jsonify({'error': 'Internal server error'}), 500
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
        return jsonify({'error': 'Missing username or task_id'}), 400
    try:
        task_id_int = int(task_id)
    except ValueError:
        return jsonify({'error': 'Invalid task_id'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM tasks WHERE username=%s AND task_id=%s",
            (username, task_id_int)
        )
        if cursor.rowcount == 0:
            return jsonify({'error': 'Task not found'}), 404
        conn.commit()
        return jsonify({'message': 'Task deleted'}), 200
    except MySQLdb.Error as e:
        app.logger.error(f"Database error in delete_task: {e}")
        return jsonify({'error': 'Internal server error'}), 500
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
        return jsonify({'error': 'Missing username, task_id, or new_task_name'}), 400
    try:
        task_id_int = int(task_id)
    except ValueError:
        return jsonify({'error': 'Invalid task_id'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET task_name=%s, task_description=%s WHERE username=%s AND task_id=%s",
            (new_task_name, new_task_description, username, task_id_int)
        )
        if cursor.rowcount == 0:
            return jsonify({'error': 'Task not found'}), 404
        conn.commit()
        return jsonify({'message': 'Task updated'}), 200
    except MySQLdb.Error as e:
        app.logger.error(f"Database error in update_task: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)