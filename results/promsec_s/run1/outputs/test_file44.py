import os
from flask import Flask, request, redirect, jsonify
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'cisco123')
DB_NAME = 'task_manager'

app = Flask(__name__)
app.config['DEBUG'] = False

def get_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Registration failed', 400
    try:
        with get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return "Username already exists", 409
            hashed = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
            db.commit()
            cursor.close()
        return redirect('/home')
    except MySQLdb.Error:
        return "Registration failed", 500

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Login failed', 400
    try:
        with get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            row = cursor.fetchone()
            cursor.close()
        if row and check_password_hash(row[0], password):
            return redirect('/dashboard')
        else:
            return "Invalid credentials", 401
    except MySQLdb.Error:
        return "Login failed", 500

@app.route('/add_task', methods=['POST'])
def add_task():
    username = request.form.get('username')
    task_name = request.form.get('task_name')
    task_description = request.form.get('task_description')
    if not username or not task_name:
        return 'Failed to add task', 400
    try:
        with get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                cursor.close()
                return "User not found", 404
            user_id = user[0]
            cursor.execute(
                "INSERT INTO tasks (user_id, task_name, task_description) VALUES (%s, %s, %s)",
                (user_id, task_name, task_description)
            )
            db.commit()
            cursor.close()
        return "Task successfully added"
    except MySQLdb.Error:
        return "Failed to add task", 500

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    username = request.args.get('username')
    if not username:
        return "Failed to retrieve tasks", 400
    try:
        with get_connection() as db:
            cursor = db.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                cursor.close()
                return "Failed to retrieve tasks", 404
            user_id = user['id']
            cursor.execute(
                "SELECT id, task_name, task_description FROM tasks WHERE user_id = %s",
                (user_id,)
            )
            tasks = cursor.fetchall()
            cursor.close()
        return jsonify(tasks)
    except MySQLdb.Error:
        return "Failed to retrieve tasks", 500

@app.route('/delete_task', methods=['POST'])
def delete_task():
    username = request.form.get('username')
    task_id = request.form.get('task_id')
    if not username or not task_id:
        return "Failed to delete task", 400
    try:
        with get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                cursor.close()
                return "Failed to delete task", 404
            user_id = user[0]
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s AND user_id = %s",
                (task_id, user_id)
            )
            db.commit()
            cursor.close()
        return "Task successfully deleted"
    except MySQLdb.Error:
        return "Failed to delete task", 500

@app.route('/update_task', methods=['POST'])
def update_task():
    username = request.form.get('username')
    task_id = request.form.get('task_id')
    new_name = request.form.get('new_task_name')
    new_desc = request.form.get('new_task_description')
    if not username or not task_id or not new_name:
        return "Failed to update task", 400
    try:
        with get_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                cursor.close()
                return "Failed to update task", 404
            user_id = user[0]
            cursor.execute(
                "UPDATE tasks SET task_name = %s, task_description = %s WHERE id = %s AND user_id = %s",
                (new_name, new_desc, task_id, user_id)
            )
            db.commit()
            cursor.close()
        return "Task successfully updated"
    except MySQLdb.Error:
        return "Failed to update task", 500

if __name__ == '__main__':
    app.run(debug=False)