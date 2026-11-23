import os
import logging
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector.pooling import MySQLConnectionPool

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

mypool = MySQLConnectionPool(pool_name="mypool", pool_size=5, host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

def get_connection():
    return mypool.get_connection()

def json_error(message, status):
    return jsonify({"error": message}), status

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return json_error("invalid json", 400)
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return json_error("username and password required", 400)
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return json_error("username already exists", 400)
        pwd_hash = generate_password_hash(password, method="pbkdf2:sha256")
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pwd_hash))
        conn.commit()
        return jsonify({"message": "user registered"}), 201
    except Exception:
        logger.exception("Error in register")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return json_error("invalid json", 400)
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return json_error("username and password required", 400)
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return json_error("invalid credentials", 401)
        return jsonify({"message": "login successful", "token": "placeholder"}), 200
    except Exception:
        logger.exception("Error in login")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/add_employee", methods=["POST"])
def add_employee():
    data = request.get_json()
    if not data:
        return json_error("invalid json", 400)
    name = data.get("name", "").strip()
    position = data.get("position", "").strip()
    department = data.get("department", "").strip()
    if not name or not position or not department:
        return json_error("name, position and department required", 400)
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (name, position, department) VALUES (%s, %s, %s)", (name, position, department))
        conn.commit()
        return jsonify({"message": "employee added"}), 201
    except Exception:
        logger.exception("Error in add_employee")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/view_employees", methods=["GET"])
def view_employees():
    department = request.args.get("department")
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if department:
            cursor.execute("SELECT * FROM employees WHERE department = %s", (department,))
        else:
            cursor.execute("SELECT * FROM employees")
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception:
        logger.exception("Error in view_employees")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/update_employee/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    data = request.get_json()
    if not data:
        return json_error("invalid json", 400)
    position = data.get("position", "").strip()
    department = data.get("department", "").strip()
    if not position or not department:
        return json_error("position and department required", 400)
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE employees SET position = %s, department = %s WHERE id = %s", (position, department, employee_id))
        if cursor.rowcount == 0:
            return json_error("employee not found", 404)
        conn.commit()
        return jsonify({"message": "employee updated"}), 200
    except Exception:
        logger.exception("Error in update_employee")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/delete_employee/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        if cursor.rowcount == 0:
            return json_error("employee not found", 404)
        conn.commit()
        return jsonify({"message": "employee deleted"}), 200
    except Exception:
        logger.exception("Error in delete_employee")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/add_department", methods=["POST"])
def add_department():
    data = request.get_json()
    if not data:
        return json_error("invalid json", 400)
    name = data.get("name", "").strip()
    manager = data.get("manager", "").strip()
    if not name or not manager:
        return json_error("name and manager required", 400)
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO departments (name, manager) VALUES (%s, %s)", (name, manager))
        conn.commit()
        return jsonify({"message": "department added"}), 201
    except Exception:
        logger.exception("Error in add_department")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/view_departments", methods=["GET"])
def view_departments():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, manager FROM departments")
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception:
        logger.exception("Error in view_departments")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/assign_project", methods=["POST"])
def assign_project():
    data = request.get_json()
    if not data:
        return json_error("invalid json", 400)
    employee_id = data.get("employee_id")
    project_name = data.get("project_name", "").strip()
    deadline = data.get("deadline", "").strip()
    if employee_id is None or not project_name or not deadline:
        return json_error("employee_id, project_name and deadline required", 400)
    try:
        employee_id = int(employee_id)
    except (ValueError, TypeError):
        return json_error("employee_id must be integer", 400)
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (employee_id, project_name, deadline) VALUES (%s, %s, %s)", (employee_id, project_name, deadline))
        conn.commit()
        return jsonify({"message": "project assigned"}), 201
    except Exception:
        logger.exception("Error in assign_project")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/view_projects", methods=["GET"])
def view_projects():
    employee_id = request.args.get("employee_id")
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if employee_id is not None:
            try:
                emp_id_int = int(employee_id)
            except ValueError:
                return json_error("employee_id must be integer", 400)
            cursor.execute("SELECT * FROM projects WHERE employee_id = %s", (emp_id_int,))
        else:
            cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception:
        logger.exception("Error in view_projects")
        return json_error("internal server error", 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "5000"))
    app.run(host=host, port=port, debug=False)