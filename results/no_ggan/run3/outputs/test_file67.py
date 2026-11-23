import os
from flask import Flask, request, redirect, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import MySQLdb.cursors

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'supersecret')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'testdb')

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST,
                           user=DB_USER,
                           password=DB_PASSWORD,
                           db=DB_NAME,
                           charset='utf8mb4',
                           cursorclass=MySQLdb.cursors.DictCursor,
                           autocommit=False)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            return 'Username already exists', 400
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('login'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if not row or not check_password_hash(row['password_hash'], password):
            return 'Invalid credentials', 401
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/add_employee', methods=['POST'])
def add_employee():
    employee_name = request.form.get('employee_name')
    position = request.form.get('position')
    department = request.form.get('department')
    if not employee_name or not position or not department:
        return 'Missing fields', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO employees (name, position, department) VALUES (%s, %s, %s)', (employee_name, position, department))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Employee added', 201

@app.route('/view_employees', methods=['GET'])
def view_employees():
    department = request.args.get('department')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if department:
            cursor.execute('SELECT * FROM employees WHERE department=%s', (department,))
        else:
            cursor.execute('SELECT * FROM employees')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return jsonify(rows), 200

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.get_json()
    if not data:
        return 'Invalid JSON', 400
    fields = []
    params = []
    if 'position' in data:
        fields.append('position=%s')
        params.append(data['position'])
    if 'department' in data:
        fields.append('department=%s')
        params.append(data['department'])
    if not fields:
        return 'No fields to update', 400
    params.append(employee_id)
    set_clause = ', '.join(fields)
    sql = f'UPDATE employees SET {set_clause} WHERE id=%s'
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, tuple(params))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Employee updated', 200

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM employees WHERE id=%s', (employee_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Employee deleted', 200

@app.route('/add_department', methods=['POST'])
def add_department():
    department_name = request.form.get('department_name')
    manager = request.form.get('manager')
    if not department_name or not manager:
        return 'Missing fields', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO departments (name, manager) VALUES (%s, %s)', (department_name, manager))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Department added', 201

@app.route('/view_departments', methods=['GET'])
def view_departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM departments')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return jsonify(rows), 200

@app.route('/assign_project', methods=['POST'])
def assign_project():
    employee_id = request.form.get('employee_id')
    project_name = request.form.get('project_name')
    deadline = request.form.get('deadline')
    if not employee_id or not project_name or not deadline:
        return 'Missing fields', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO projects (employee_id, name, deadline) VALUES (%s, %s, %s)', (employee_id, project_name, deadline))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Project assigned', 201

@app.route('/view_projects', methods=['GET'])
def view_projects():
    employee_id = request.args.get('employee_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if employee_id:
            cursor.execute('SELECT * FROM projects WHERE employee_id=%s', (employee_id,))
        else:
            cursor.execute('SELECT * FROM projects')
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return jsonify(rows), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return 'Welcome to the dashboard', 200

if __name__ == '__main__':
    app.run(debug=False)