from flask import Flask, request, redirect, jsonify
import re
import hashlib
import MySQLdb
import os

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    conn = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return redirect("/login", code=307)
        salt_bytes = os.urandom(16)
        salt_hex = salt_bytes.hex()
        pwd_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
        cursor.execute(
            "INSERT INTO users(username, password, salt, account_created) VALUES (%s, %s, %s, %s)",
            (username, pwd_hash, salt_hex, 1)
        )
        conn.commit()
        return "Registration successful"
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password, salt FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            stored_hash, stored_salt_hex = row
            salt_bytes = bytes.fromhex(stored_salt_hex)
            pwd_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
            if pwd_hash == stored_hash:
                return redirect("/dashboard", code=307)
        return "Invalid credentials"
    finally:
        cursor.close()
        conn.close()

@app.route('/project/create', methods=['POST'])
def create_project():
    username = request.form['username']
    project_name = request.form['project_name']
    conn = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.execute(
                "INSERT INTO projects(username, project_name) VALUES (%s, %s)",
                (username, project_name)
            )
            conn.commit()
            return "Project created successfully"
        else:
            return "User not found"
    finally:
        cursor.close()
        conn.close()

@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = request.form['project_name']
    task_name = request.form['task_name']
    task_description = request.form['task_description']
    conn = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT project_name FROM projects WHERE project_name = %s", (project_name,))
        if cursor.fetchone():
            cursor.execute(
                "INSERT INTO tasks(project_name, task_name, task_description) VALUES (%s, %s, %s)",
                (project_name, task_name, task_description)
            )
            conn.commit()
            return "Task added successfully"
        else:
            return "Project not found"
    finally:
        cursor.close()
        conn.close()

@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name')
    conn = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT task_name, task_description FROM tasks WHERE project_name = %s",
            (project_name,)
        )
        rows = cursor.fetchall()
        tasks = [{'task_name': row[0], 'task_description': row[1]} for row in rows]
        return jsonify(tasks)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)