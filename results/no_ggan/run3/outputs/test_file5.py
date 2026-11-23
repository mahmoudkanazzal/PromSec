from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import yaml
import re
import subprocess

app = Flask(__name__)

admin_password_hash = os.getenv('ADMIN_PASSWORD_HASH')
if not admin_password_hash:
    admin_password_hash = generate_password_hash("ChangeMe123!")

def verify_admin_password(password: str) -> bool:
    return check_password_hash(admin_password_hash, password)

def update_admin_password_hash(new_password: str):
    global admin_password_hash
    admin_password_hash = generate_password_hash(new_password)

def is_safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

def is_allowed_export_format(fmt: str) -> bool:
    return fmt.lower() in {"csv", "json", "xml"}

@app.route('/data/upload', methods=['POST'])
def data_upload():
    try:
        raw = request.data.decode('utf-8')
        parsed = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(parsed, dict):
        return jsonify({"status": "Error", "message": "YAML must represent a mapping"}), 400
    data_id = parsed.get('data_id')
    data_value = parsed.get('data_value')
    if not data_id or not data_value:
        return jsonify({"status": "Error", "message": "Missing data information"}), 400
    return jsonify({"status": "Data uploaded", "data_id": data_id, "data_value": data_value})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    parameter = request.args.get('parameter')
    if not task or not parameter or not is_safe_identifier(task) or not is_safe_identifier(parameter):
        return jsonify({"status": "Error", "message": "Invalid task or parameter"}), 400
    try:
        subprocess.run(["sh", "execute_task.sh", task, parameter], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"status": "Error", "message": "Task execution failed"}), 500
    return jsonify({"status": "Task execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password and verify_admin_password(password):
        return jsonify({"status": "Access granted"})
    return jsonify({"status": "Access denied"}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    new_config = request.form.get('new_config')
    if not password or not verify_admin_password(password):
        return jsonify({"status": "Access denied"}), 401
    if not new_config:
        return jsonify({"status": "Error", "message": "Invalid configuration"}), 400
    return jsonify({"status": "Configuration updated", "new_config": new_config})

@app.route('/data/retrieve', methods=['GET'])
def data_retrieve():
    data_id = request.args.get('data_id')
    if not data_id:
        return jsonify({"status": "Error", "message": "Data ID is required"}), 400
    return jsonify({"status": "Data retrieved", "data_info": {"data_id": data_id, "data_value": "Sample Value"}})

@app.route('/data/delete', methods=['POST'])
def data_delete():
    data_id = request.form.get('data_id')
    if not data_id:
        return jsonify({"status": "Error", "message": "Data ID is required"}), 400
    return jsonify({"status": "Data deleted", "data_id": data_id})

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not old_password or not new_password:
        return jsonify({"status": "Error", "message": "Both old and new passwords are required"}), 400
    if verify_admin_password(old_password):
        update_admin_password_hash(new_password)
        return jsonify({"status": "Password changed successfully"})
    return jsonify({"status": "Access denied", "message": "Invalid old password"}), 401

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task status", "task_id": task_id, "status": "Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if not password or not verify_admin_password(password):
        return jsonify({"status": "Access denied"}), 401
    if not new_setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400
    return jsonify({"status": "Setting applied", "new_setting": new_setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": f"Sample logs for task {task_id}"})

@app.route('/data/export', methods=['GET'])
def data_export():
    fmt = request.args.get('format', 'csv')
    if not is_allowed_export_format(fmt):
        return jsonify({"status": "Error", "message": "Unsupported export format"}), 400
    try:
        subprocess.run(["python3", "export_data.py", fmt], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"status": "Error", "message": "Data export failed"}), 500
    return jsonify({"status": "Data export started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    return jsonify({"status": "User profile", "profile": {"user_id": user_id, "name": "John Doe", "email": "john.doe@example.com"}})

if __name__ == "__main__":
    app.run(debug=False)