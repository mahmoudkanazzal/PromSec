import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    # Register user code here
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    # Login user code here
    return jsonify({'message': 'User logged in successfully'})

@app.route('/create_project', methods=['POST'])
def create_project():
    # Create project code here
    return jsonify({'message': 'Project created successfully'})

@app.route('/add_task', methods=['POST'])
def add_task():
    # Add task code here
    return jsonify({'message': 'Task added successfully'})

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    # View tasks code here
    return jsonify({'message': 'Tasks retrieved successfully'})

if __name__ == '__main__':
    app.run()
