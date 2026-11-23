import os
from flask import Flask, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    return jsonify({'error': 'Username already exists'}), 400
                pwd_hash = generate_password_hash(password)
                cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
                conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
                if row and check_password_hash(row['password_hash'], password):
                    return redirect(url_for('dashboard'))
                else:
                    return jsonify({'error': 'Invalid credentials'}), 401
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard')
def dashboard():
    return jsonify({'message': 'Welcome to the dashboard'})

@app.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.get_json() or {}
    name = data.get('employee_name')
    position = data.get('position')
    department = data.get('department')
    if not name or not position or not department:
        return jsonify({'error': 'Missing employee data'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO employees (employee_name, position, department) VALUES (%s, %s, %s)', (name, position, department))
                conn.commit()
        return jsonify({'message': 'Employee added'}), 201
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_employees', methods=['GET'])
def view_employees():
    department = request.args.get('department')
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if department:
                    cur.execute('SELECT * FROM employees WHERE department=%s', (department,))
                else:
                    cur.execute('SELECT * FROM employees')
                rows = cur.fetchall()
        return jsonify(rows), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.get_json() or {}
    position = data.get('position')
    department = data.get('department')
    if not position or not department:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE employees SET position=%s, department=%s WHERE id=%s', (position, department, employee_id))
                conn.commit()
                if cur.rowcount == 0:
                    return jsonify({'error': 'Employee not found'}), 404
        return jsonify({'message': 'Employee updated'}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM employees WHERE id=%s', (employee_id,))
                conn.commit()
                if cur.rowcount == 0:
                    return jsonify({'error': 'Employee not found'}), 404
        return jsonify({'message': 'Employee deleted'}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/add_department', methods=['POST'])
def add_department():
    data = request.get_json() or {}
    name = data.get('department_name')
    manager = data.get('manager')
    if not name or not manager:
        return jsonify({'error': 'Missing department data'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO departments (department_name, manager) VALUES (%s, %s)', (name, manager))
                conn.commit()
        return jsonify({'message': 'Department added'}), 201
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_departments', methods=['GET'])
def view_departments():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM departments')
                rows = cur.fetchall()
        return jsonify(rows), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/assign_project', methods=['POST'])
def assign_project():
    data = request.get_json() or {}
    employee_id = data.get('employee_id')
    project_name = data.get('project_name')
    deadline = data.get('deadline')
    if not employee_id or not project_name or not deadline:
        return jsonify({'error': 'Missing project data'}), 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO projects (employee_id, project_name, deadline) VALUES (%s, %s, %s)', (employee_id, project_name, deadline))
                conn.commit()
        return jsonify({'message': 'Project assigned'}), 201
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_projects', methods=['GET'])
def view_projects():
    employee_id = request.args.get('employee_id')
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if employee_id:
                    cur.execute('SELECT * FROM projects WHERE employee_id=%s', (employee_id,))
                else:
                    cur.execute('SELECT * FROM projects')
                rows = cur.fetchall()
        return jsonify(rows), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False)