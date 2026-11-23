import os
import hashlib
from flask import Flask, request, redirect, jsonify, abort, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'test')

def get_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', cursorclass=MySQLdb.cursors.DictCursor, autocommit=False)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    pwd_hash = generate_password_hash(password)
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM employees WHERE username=%s', (username,))
        if cur.fetchone():
            return redirect(url_for('register'))
        cur.execute('INSERT INTO employees (username, password) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return redirect(url_for('login'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT password FROM employees WHERE username=%s', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row['password'], password):
            return redirect(url_for('dashboard'))
        return 'Invalid credentials', 401
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/add_employee', methods=['POST'])
def add_employee():
    employee_name = request.form.get('employee_name')
    position = request.form.get('position')
    department = request.form.get('department')
    if not employee_name or not position or not department:
        abort(400)
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO employees (employee_name, position, department) VALUES (%s, %s, %s)', (employee_name, position, department))
        conn.commit()
        return 'Employee added successfully', 201
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_employees', methods=['GET'])
def view_employees():
    department = request.args.get('department')
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if department:
            cur.execute('SELECT * FROM employees WHERE department=%s', (department,))
        else:
            cur.execute('SELECT * FROM employees')
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.get_json()
    if not data:
        abort(400)
    position = data.get('position')
    department = data.get('department')
    if not position or not department:
        abort(400)
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('UPDATE employees SET position=%s, department=%s WHERE id=%s', (position, department, employee_id))
        if cur.rowcount == 0:
            abort(404)
        conn.commit()
        return 'Employee updated successfully', 200
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM employees WHERE id=%s', (employee_id,))
        if cur.rowcount == 0:
            abort(404)
        conn.commit()
        return 'Employee deleted successfully', 200
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/add_department', methods=['POST'])
def add_department():
    department_name = request.form.get('department_name')
    manager = request.form.get('manager')
    if not department_name or not manager:
        abort(400)
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO departments (department_name, manager) VALUES (%s, %s)', (department_name, manager))
        conn.commit()
        return 'Department added successfully', 201
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_departments', methods=['GET'])
def view_departments():
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM departments')
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/assign_project', methods=['POST'])
def assign_project():
    employee_id = request.form.get('employee_id')
    project_name = request.form.get('project_name')
    deadline = request.form.get('deadline')
    if not employee_id or not project_name or not deadline:
        abort(400)
    try:
        employee_id_int = int(employee_id)
    except ValueError:
        abort(400)
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO projects (employee_id, project_name, deadline) VALUES (%s, %s, %s)', (employee_id_int, project_name, deadline))
        conn.commit()
        return 'Project assigned successfully', 201
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_projects', methods=['GET'])
def view_projects():
    employee_id = request.args.get('employee_id')
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if employee_id:
            try:
                employee_id_int = int(employee_id)
            except ValueError:
                abort(400)
            cur.execute('SELECT * FROM projects WHERE employee_id=%s', (employee_id_int,))
        else:
            cur.execute('SELECT * FROM projects')
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return 'Welcome to the dashboard'

if __name__ == '__main__':
    app.run(debug=False)