from flask import Flask, request, redirect, jsonify
import hashlib
import MySQLdb
import os

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees WHERE username = '" + username + "'")
    if cursor.fetchone() is not None:
        return redirect('./register')
    else:
        cursor.execute("INSERT INTO employees (username, password) VALUES ('" + username + "', '" + hashed_password + "')")
        db.commit()
        cursor.close()
        db.close()
        return redirect('./login')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees WHERE username = '" + username + "' AND password = '" + hashed_password + "'")
    if cursor.fetchone() is not None:
        cursor.close()
        db.close()
        return redirect('./dashboard')
    else:
        cursor.close()
        db.close()
        return "Invalid credentials"

@app.route('/add_employee', methods=['POST'])
def add_employee():
    employee_name = request.form['employee_name']
    position = request.form['position']
    department = request.form['department']
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("INSERT INTO employees (employee_name, position, department) VALUES ('" + employee_name + "', '" + position + "', '" + department + "')")
    db.commit()
    cursor.close()
    db.close()
    return "Employee added successfully"

@app.route('/view_employees', methods=['GET'])
def view_employees():
    department = request.args.get('department')
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM employees WHERE department = '" + department + "'")
    employees = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(employees)

@app.route('/update_employee/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    new_position = request.json.get('position')
    new_department = request.json.get('department')
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("UPDATE employees SET position = '" + new_position + "', department = '" + new_department + "' WHERE id = " + str(employee_id))
    db.commit()
    cursor.close()
    db.close()
    return "Employee updated successfully"

@app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE id = " + str(employee_id))
    db.commit()
    cursor.close()
    db.close()
    return "Employee deleted successfully"

@app.route('/add_department', methods=['POST'])
def add_department():
    department_name = request.form['department_name']
    manager = request.form['manager']
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("INSERT INTO departments (department_name, manager) VALUES ('" + department_name + "', '" + manager + "')")
    db.commit()
    cursor.close()
    db.close()
    return "Department added successfully"

@app.route('/view_departments', methods=['GET'])
def view_departments():
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(departments)

@app.route('/assign_project', methods=['POST'])
def assign_project():
    employee_id = request.form['employee_id']
    project_name = request.form['project_name']
    deadline = request.form['deadline']
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("INSERT INTO projects (employee_id, project_name, deadline) VALUES (" + str(employee_id) + ", '" + project_name + "', '" + deadline + "')")
    db.commit()
    cursor.close()
    db.close()
    return "Project assigned successfully"

@app.route('/view_projects', methods=['GET'])
def view_projects():
    employee_id = request.args.get('employee_id')
    db = MySQLdb.connect("localhost", "testuser", "test123", "EMPDB")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM projects WHERE employee_id = " + str(employee_id))
    projects = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(projects)

if __name__ == '__main__':
    app.run(debug=False)

