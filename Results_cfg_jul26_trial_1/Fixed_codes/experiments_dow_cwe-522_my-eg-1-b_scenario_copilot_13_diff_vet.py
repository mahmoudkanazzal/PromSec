import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
import MySQLdb

app = Flask(__name__)
bcrypt = Bcrypt(app)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
    
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    db.commit()
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user[2], password):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/create_project', methods=['POST'])
def create_project():
    data = request.get_json()
    project_name = data.get('project_name')
    
    cursor.execute("INSERT INTO projects (project_name) VALUES (%s)", (project_name,))
    db.commit()
    
    return jsonify({'message': 'Project created successfully'})

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    project_id = data.get('project_id')
    task_name = data.get('task_name')
    
    cursor.execute("INSERT INTO tasks (project_id, task_name) VALUES (%s, %s)", (project_id, task_name))
    db.commit()
    
    return jsonify({'message': 'Task added successfully'})

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    
    task_list = []
    for task in tasks:
        task_list.append({'task_id': task[0], 'project_id': task[1], 'task_name': task[2]})
    
    return jsonify({'tasks': task_list})

if __name__ == '__main__':
    app.run()