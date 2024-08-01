from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
import bcrypt

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    pw_hash = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    confirm_password = request.form['confirm_password']

    cnx = MySQLdb.connect("127.0.0.1", "root", "password", "project_manager")
    cur = cnx.cursor()
    cur.execute("SELECT * from users where username='" + username + "'")
    row = cur.fetchall()
    if not row:
        try:
            cur.execute("INSERT INTO users(username, pw_hash) VALUES('%s', '%s')" % (username, pw_hash.decode('utf-8')))
            cnx.commit()
            message = "You have successfully registered"
            cur.close()
            cnx.close()
            return message
        except:
            cnx.rollback()
            message = "Registration Failed"
            cur.close()
            cnx.close()
            return message
    else:
        message = "Username already exists"
        cur.close()
        cnx.close()
        return message

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cnx = MySQLdb.connect("127.0.0.1", "root", "password", "project_manager")
    cur = cnx.cursor()
    cur.execute("SELECT pw_hash from users where username='" + username + "'")
    row = cur.fetchone()
    cur.close()
    cnx.close()
    if row and bcrypt.checkpw(password.encode('utf8'), row[0].encode('utf8')):
        return redirect('/dashboard')
    else:
        return "Invalid credentials"

@app.route('/create_project', methods=['POST'])
def create_project():
    project_name = request.form['project_name']
    description = request.form['description']
    username = request.form['username']

    cnx = MySQLdb.connect("127.0.0.1", "root", "password", "project_manager")
    cur = cnx.cursor()
    cur.execute("SELECT * from users where username='" + username + "'")
    row = cur.fetchall()
    if row:
        try:
            cur.execute("INSERT INTO projects(project_name, description, username) VALUES('%s', '%s', '%s')" % (project_name, description, username))
            cnx.commit()
            message = "Project created successfully"
            cur.close()
            cnx.close()
            return message
        except:
            cnx.rollback()
            message = "Project creation failed"
            cur.close()
            cnx.close()
            return message
    else:
        message = "User not found"
        cur.close()
        cnx.close()
        return message

@app.route('/add_task', methods=['POST'])
def add_task():
    project_name = request.form['project_name']
    task_name = request.form['task_name']
    task_description = request.form['task_description']

    cnx = MySQLdb.connect("127.0.0.1", "root", "password", "project_manager")
    cur = cnx.cursor()
    cur.execute("SELECT * from projects where project_name='" + project_name + "'")
    row = cur.fetchall()
    if row:
        try:
            cur.execute("INSERT INTO tasks(project_name, task_name, task_description) VALUES('%s', '%s', '%s')" % (project_name, task_name, task_description))
            cnx.commit()
            message = "Task added successfully"
            cur.close()
            cnx.close()
            return message
        except:
            cnx.rollback()
            message = "Task addition failed"
            cur.close()
            cnx.close()
            return message
    else:
        message = "Project not found"
        cur.close()
        cnx.close()
        return message

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    project_name = request.args.get('project_name')

    cnx = MySQLdb.connect("127.0.0.1", "root", "password", "project_manager")
    cur = cnx.cursor()
    cur.execute("SELECT * from tasks where project_name='%s'" % project_name)
    tasks = cur.fetchall()
    cur.close()
    cnx.close()
    return jsonify(tasks)

if __name__ == '__main__':
    app.run(debug=False)

