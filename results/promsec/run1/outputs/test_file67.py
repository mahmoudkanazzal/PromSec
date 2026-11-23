import os
import hashlib
import json
import logging
import MySQLdb
from flask import Flask, request, jsonify, redirect, url_for
from contextlib import closing

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset='utf8mb4',
        cursorclass=MySQLdb.cursors.DictCursor
    )

def hash_password(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    pw_hash = hash_password(password)
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    return redirect(url_for('register')), 302
                cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pw_hash))
                conn.commit()
        return redirect(url_for('login')), 302
    except MySQLdb.Error:
        logging.exception('Database error during registration')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    pw_hash = hash_password(password)
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
                if row and row['password_hash'] == pw_hash:
                    return redirect(url_for('dashboard')), 302
                else:
                    return jsonify({'error': 'Invalid credentials'}), 401
    except MySQLdb.Error:
        logging.exception('Database error during login')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard')
def dashboard():
    return jsonify({'message': 'Welcome to the dashboard'}), 200

@app.route('/add_employee', methods=['POST'])
def add_employee():
    name = request.form.get('employee_name')
    position = request.form.get('position')
    department = request.form.get('department')
    if not name or not position or not department:
        return jsonify({'error': 'Missing employee data'}), 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO employees (employee_name, position, department) VALUES (%s, %s, %s)',
                    (name, position, department)
                )
                conn.commit()
        return jsonify({'message': 'Employee added'}), 201
    except MySQLdb.Error:
        logging.exception('Database error during add_employee')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_employees', methods=['GET'])
def view_employees():
    dept = request.args.get('department')
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                if dept:
                    cur.execute('SELECT * FROM employees WHERE department=%s', (dept,))
                else:
                    cur.execute('SELECT * FROM employees')
                rows = cur.fetchall()
        return jsonify(rows), 200
    except MySQLdb.Error:
        logging.exception('Database error during view_employees')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400
    position = data.get('position')
    department = data.get('department')
    if not position or not department:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'UPDATE employees SET position=%s, department=%s WHERE employee_id=%s',
                    (position, department, employee_id)
                )
                conn.commit()
                if cur.rowcount == 0:
                    return jsonify({'error': 'Employee not found'}), 404
        return jsonify({'message': 'Employee updated'}), 200
    except MySQLdb.Error:
        logging.exception('Database error during update_employee')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('DELETE FROM employees WHERE employee_id=%s', (employee_id,))
                conn.commit()
                if cur.rowcount == 0:
                    return jsonify({'error': 'Employee not found'}), 404
        return jsonify({'message': 'Employee deleted'}), 200
    except MySQLdb.Error:
        logging.exception('Database error during delete_employee')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/add_department', methods=['POST'])
def add_department():
    name = request.form.get('department_name')
    manager = request.form.get('manager')
    if not name or not manager:
        return jsonify({'error': 'Missing department data'}), 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO departments (department_name, manager) VALUES (%s, %s)',
                    (name, manager)
                )
                conn.commit()
        return jsonify({'message': 'Department added'}), 201
    except MySQLdb.Error:
        logging.exception('Database error during add_department')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_departments', methods=['GET'])
def view_departments():
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT * FROM departments')
                rows = cur.fetchall()
        return jsonify(rows), 200
    except MySQLdb.Error:
        logging.exception('Database error during view_departments')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/assign_project', methods=['POST'])
def assign_project():
    employee_id = request.form.get('employee_id')
    project_name = request.form.get('project_name')
    deadline = request.form.get('deadline')
    if not employee_id or not project_name or not deadline:
        return jsonify({'error': 'Missing project data'}), 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO projects (employee_id, project_name, deadline) VALUES (%s, %s, %s)',
                    (employee_id, project_name, deadline)
                )
                conn.commit()
        return jsonify({'message': 'Project assigned'}), 201
    except MySQLdb.Error:
        logging.exception('Database error during assign_project')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_projects', methods=['GET'])
def view_projects():
    emp_id = request.args.get('employee_id')
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                if emp_id:
                    cur.execute('SELECT * FROM projects WHERE employee_id=%s', (emp_id,))
                else:
                    cur.execute('SELECT * FROM projects')
                rows = cur.fetchall()
        return jsonify(rows), 200
    except MySQLdb.Error:
        logging.exception('Database error during view_projects')
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False)