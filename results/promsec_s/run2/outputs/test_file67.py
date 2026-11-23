import os
from flask import Flask, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'testdb')
}

def get_connection():
    return mysql.connector.connect(**db_config)

@app.route('/register', methods=['POST'])
def register():
    data = request.form or request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing fields'}), 400
    hashed = generate_password_hash(password)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed))
        conn.commit()
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'User already exists'}), 400
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('view_employees'))

@app.route('/login', methods=['POST'])
def login():
    data = request.form or request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing fields'}), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return redirect(url_for('view_employees'))
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.form or request.get_json() or {}
    name = data.get('name')
    department_id = data.get('department_id')
    if not name or not department_id:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO employees (name, department_id) VALUES (%s, %s)', (name, department_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Employee added'}), 201

@app.route('/view_employees', methods=['GET'])
def view_employees():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM employees')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.get_json() or {}
    name = data.get('name')
    department_id = data.get('department_id')
    if not name and not department_id:
        return jsonify({'error': 'No fields to update'}), 400
    fields = []
    values = []
    if name:
        fields.append('name = %s')
        values.append(name)
    if department_id:
        fields.append('department_id = %s')
        values.append(department_id)
    values.append(employee_id)
    query = f'UPDATE employees SET {", ".join(fields)} WHERE id = %s'
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Employee updated'}), 200

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM employees WHERE id = %s', (employee_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Employee deleted'}), 200

@app.route('/add_department', methods=['POST'])
def add_department():
    data = request.form or request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Missing name'}), 400
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO departments (name) VALUES (%s)', (name,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Department added'}), 201

@app.route('/view_departments', methods=['GET'])
def view_departments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM departments')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

@app.route('/assign_project', methods=['POST'])
def assign_project():
    data = request.form or request.get_json() or {}
    employee_id = data.get('employee_id')
    project_name = data.get('project_name')
    if not employee_id or not project_name:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO projects (name, employee_id) VALUES (%s, %s)', (project_name, employee_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return jsonify({'message': 'Project assigned'}), 201

@app.route('/view_projects', methods=['GET'])
def view_projects():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM projects')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows), 200

if __name__ == '__main__':
    app.run(debug=False)