import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
import MySQLdb

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQLdb.connect(host=app.config['MYSQL_HOST'], user=app.config['MYSQL_USER'], password=app.config['MYSQL_PASSWORD'], database=app.config['MYSQL_DB'])
cursor = mysql.cursor()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    mysql.commit()
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user[2], password):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/create_project', methods=['POST'])
def create_project():
    data = request.get_json()
    project_name = data['project_name']
    
    cursor.execute("INSERT INTO projects (project_name) VALUES (%s)", (project_name,))
    mysql.commit()
    
    return jsonify({'message': 'Project created successfully'})

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    project_id = data['project_id']
    task_name = data['task_name']
    
    cursor.execute("INSERT INTO tasks (project_id, task_name) VALUES (%s, %s)", (project_id, task_name))
    mysql.commit()
    
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