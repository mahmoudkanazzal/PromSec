import os
from flask import Flask, request, jsonify
import hashlib
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host=os.environ.get('DB_HOST'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    database=os.environ.get('DB_NAME')
)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    db.commit()
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_password))
    user = cursor.fetchone()
    
    if user:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/employees', methods=['GET'])
def get_employees():
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    
    return jsonify({'employees': employees})

@app.route('/departments', methods=['GET'])
def get_departments():
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    
    return jsonify({'departments': departments})

@app.route('/projects', methods=['GET'])
def get_projects():
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    
    return jsonify({'projects': projects})

if __name__ == '__main__':
    app.run()
