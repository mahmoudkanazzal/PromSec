from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    salt = os.urandom(16)
    hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    user_name_regex = "^" + username + "$"
    db = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = db.cursor()
    sql = "select username from users where username like '%s'" % user_name_regex
    cursor.execute(sql)
    data = cursor.fetchall()
    if data:
        return redirect("/login", code=307)
    else:
        sql = "insert into users(username, password, salt, account_created) values ('%s','%s', '%s', %d)" % (username, hashed_password, salt.hex(), 1)
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()
        return "Registration successful"

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = db.cursor()
    sql = "select password, salt from users where username = '%s'" % username
    cursor.execute(sql)
    data = cursor.fetchone()
    if data:
        stored_password, salt = data
        salt = bytes.fromhex(salt)
        hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
        if hashed_password == stored_password:
            return redirect("/dashboard", code=307)
    return "Invalid credentials"

@app.route('/project/create', methods=['POST'])
def create_project():
    username = request.form['username']
    project_name = request.form['project_name']
    db = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = db.cursor()
    sql = "select username from users where username = '%s'" % username
    cursor.execute(sql)
    data = cursor.fetchone()
    if data:
        sql = "insert into projects(username, project_name) values ('%s', '%s')" % (username, project_name)
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()
        return "Project created successfully"
    return "User not found"

@app.route('/task/add', methods=['POST'])
def add_task():
    project_name = request.form['project_name']
    task_name = request.form['task_name']
    task_description = request.form['task_description']
    db = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = db.cursor()
    sql = "select project_name from projects where project_name = '%s'" % project_name
    cursor.execute(sql)
    data = cursor.fetchone()
    if data:
        sql = "insert into tasks(project_name, task_name, task_description) values ('%s', '%s', '%s')" % (project_name, task_name, task_description)
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()
        return "Task added successfully"
    return "Project not found"

@app.route('/tasks/view', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name')
    db = MySQLdb.connect("localhost", "root", "", "projectdb")
    cursor = db.cursor()
    sql = "select task_name, task_description from tasks where project_name = '%s'" % project_name
    cursor.execute(sql)
    tasks = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(tasks)

if __name__ == '__main__':
    app.run(debug=False)

