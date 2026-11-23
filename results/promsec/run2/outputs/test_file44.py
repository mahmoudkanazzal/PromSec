from __future__ import annotations
import os
import pymysql
from flask import Flask, request, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    db = os.getenv('DB_NAME')
    if not all([host, user, password, db]):
        raise RuntimeError("Database configuration error")
    connect_kwargs = {
        'host': host,
        'user': user,
        'password': password,
        'database': db,
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': False
    }
    ssl_ca = os.getenv('DB_SSL_CA')
    if ssl_ca:
        connect_kwargs['ssl'] = {'ca': ssl_ca}
    return pymysql.connect(**connect_kwargs)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Registration failed"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return "Registration failed"
            pwd_hash = generate_password_hash(password)
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pwd_hash))
            conn.commit()
            return redirect('/home')
        except Exception:
            conn.rollback()
            return "Registration failed"
        finally:
            cur.close()
            conn.close()
    except Exception:
        return "Registration failed"

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Invalid credentials"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            if not row or not check_password_hash(row[0], password):
                return "Invalid credentials"
            return redirect('/dashboard')
        except Exception:
            return "Login failed"
        finally:
            cur.close()
            conn.close()
    except Exception:
        return "Login failed"

@app.route('/add_task', methods=['POST'])
def add_task():
    username = request.form.get('username')
    task_name = request.form.get('task_name')
    task_description = request.form.get('task_description')
    if not username or not task_name or not task_description:
        return "Failed to add task"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if not cur.fetchone():
                return "Failed to add task"
            cur.execute("INSERT INTO tasks (username, task_name, task_description) VALUES (%s, %s, %s)", (username, task_name, task_description))
            conn.commit()
            return "Task successfully added"
        except Exception:
            conn.rollback()
            return "Failed to add task"
        finally:
            cur.close()
            conn.close()
    except Exception:
        return "Failed to add task"

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    username = request.args.get('username')
    if not username:
        return "Failed to retrieve tasks"
    try:
        conn = get_db_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cur.execute("SELECT task_id, username, task_name, task_description FROM tasks WHERE username = %s", (username,))
            rows = cur.fetchall()
            return jsonify(rows)
        except Exception:
            return "Failed to retrieve tasks"
        finally:
            cur.close()
            conn.close()
    except Exception:
        return "Failed to retrieve tasks"

@app.route('/delete_task', methods=['POST'])
def delete_task():
    username = request.form.get('username')
    task_id = request.form.get('task_id')
    if not username or not task_id:
        return "Failed to delete task"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM tasks WHERE username = %s AND task_id = %s", (username, task_id))
            conn.commit()
            if cur.rowcount > 0:
                return "Task successfully deleted"
            return "Failed to delete task"
        except Exception:
            conn.rollback()
            return "Failed to delete task"
        finally:
            cur.close()
            conn.close()
    except Exception:
        return "Failed to delete task"

@app.route('/update_task', methods=['POST'])
def update_task():
    username = request.form.get('username')
    task_id = request.form.get('task_id')
    new_task_name = request.form.get('new_task_name')
    new_task_description = request.form.get('new_task_description')
    if not username or not task_id or not new_task_name or not new_task_description:
        return "Failed to update task"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE tasks SET task_name = %s, task_description = %s WHERE username = %s AND task_id = %s", (new_task_name, new_task_description, username, task_id))
            conn.commit()
            if cur.rowcount > 0:
                return "Task successfully updated"
            return "Failed to update task"
        except Exception:
            conn.rollback()
            return "Failed to update task"
        finally:
            cur.close()
            conn.close()
    except Exception:
        return "Failed to update task"

if __name__ == '__main__':
    app.run(debug=False)