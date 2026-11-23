import os
from flask import Flask, request, abort, redirect, jsonify
import MySQLdb
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'testdb')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', cursorclass=MySQLdb.cursors.DictCursor)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Missing username or password')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM employees WHERE username = %s', (username,))
        if cur.fetchone():
            return redirect('./register')
        pwd_hash = generate_password_hash(password)
        cur.execute('INSERT INTO employees (username, password) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return redirect('./login')
    finally:
        cur.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Missing username or password')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT password FROM employees WHERE username = %s', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row['password'], password):
            return redirect('./dashboard')
        return 'Invalid credentials', 401
    finally:
        cur.close()
        conn.close()

@app.route('/add_employee', methods=['POST'])
def add_employee():
    name = request.form.get('employee_name')
    position = request.form.get('position')
    department = request.form.get('department')
    if not name or not position or not department:
        abort(400, description='Missing employee_name, position, or department')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO employees (employee_name, position, department) VALUES (%s, %s, %s)', (name, position, department))
        conn.commit()
        return 'Employee added successfully', 201
    finally:
        cur.close()
        conn.close()

@app.route('/view_employees', methods=['GET'])
def view_employees():
    dept = request.args.get('department')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if dept:
            cur.execute('SELECT * FROM employees WHERE department = %s', (dept,))
        else:
            cur.execute('SELECT * FROM employees')
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        cur.close()
        conn.close()

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.get_json()
    if not data:
        abort(400, description='Invalid JSON')
    fields = {}
    if 'position' in data:
        fields['position'] = data['position']
    if 'department' in data:
        fields['department'] = data['department']
    if not fields:
        abort(400, description='No fields to update')
    set_clause = ', '.join(f"{k} = %s" for k in fields)
    params = list(fields.values()) + [employee_id]
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(f'UPDATE employees SET {set_clause} WHERE id = %s', params)
        conn.commit()
        return 'Employee updated successfully', 200
    finally:
        cur.close()
        conn.close()

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM employees WHERE id = %s', (employee_id,))
        conn.commit()
        return 'Employee deleted successfully', 200
    finally:
        cur.close()
        conn.close()

@app.route('/add_department', methods=['POST'])
def add_department():
    name = request.form.get('department_name')
    manager = request.form.get('manager')
    if not name or not manager:
        abort(400, description='Missing department_name or manager')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO departments (department_name, manager) VALUES (%s, %s)', (name, manager))
        conn.commit()
        return 'Department added successfully', 201
    finally:
        cur.close()
        conn.close()

@app.route('/view_departments', methods=['GET'])
def view_departments():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM departments')
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        cur.close()
        conn.close()

@app.route('/assign_project', methods=['POST'])
def assign_project():
    employee_id = request.form.get('employee_id')
    project_name = request.form.get('project_name')
    deadline = request.form.get('deadline')
    if not employee_id or not project_name or not deadline:
        abort(400, description='Missing employee_id, project_name, or deadline')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO projects (employee_id, project_name, deadline) VALUES (%s, %s, %s)', (employee_id, project_name, deadline))
        conn.commit()
        return 'Project assigned successfully', 201
    finally:
        cur.close()
        conn.close()

@app.route('/view_projects', methods=['GET'])
def view_projects():
    emp_id = request.args.get('employee_id')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if emp_id:
            cur.execute('SELECT * FROM projects WHERE employee_id = %s', (emp_id,))
        else:
            cur.execute('SELECT * FROM projects')
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)