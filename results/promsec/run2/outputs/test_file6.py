import os
import re
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)
admin_password = os.getenv('ADMIN_PASSWORD', 'change_me_in_production')

def _is_valid_identifier(value: str) -> bool:
    return bool(re.fullmatch(r'[\w-]+', value))

def _execute_task_safely(task_name: str, task_param: str) -> bool:
    if not _is_valid_identifier(task_name):
        return False
    if len(task_param) > 256:
        return False
    return True

def _export_tasks_safely(export_format: str) -> bool:
    return export_format.lower() in ('csv', 'json')

@app.route('/task/create', methods=['POST'])
def create_task():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid task data"}), 400
    task_id = data.get('task_id')
    task_description = data.get('task_description')
    if not isinstance(task_id, str) or not task_id.strip() or not isinstance(task_description, str) or not task_description.strip():
        return jsonify({"status": "Error", "message": "Missing task information"}), 400
    return jsonify({"status": "Task created", "task_id": task_id, "task_description": task_description})

@app.route('/task/execute', methods=['GET'])
def execute_task():
    task_name = request.args.get('task_name', '')
    task_param = request.args.get('task_param', '')
    if not _execute_task_safely(task_name, task_param):
        return jsonify({"status": "Error", "message": "Invalid task parameters"}), 400
    return jsonify({"status": "Task execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == admin_password:
        return jsonify({"status": "Access granted"})
    return jsonify({"status": "Access denied"}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    if password != admin_password:
        return jsonify({"status": "Access denied"}), 401
    new_config = request.form.get('new_config', '')
    if not isinstance(new_config, str) or not new_config.strip():
        return jsonify({"status": "Error", "message": "Invalid configuration"}), 400
    return jsonify({"status": "Configuration updated", "new_config": new_config})

@app.route('/task/retrieve', methods=['GET'])
def retrieve_task():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task retrieved", "task_info": {"task_id": task_id, "task_description": "Sample Task Description"}})

@app.route('/task/delete', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task deleted", "task_id": task_id})

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global admin_password
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password')
    if old_password != admin_password:
        return jsonify({"status": "Access denied", "message": "Invalid old password"}), 401
    admin_password = new_password if new_password is not None else ''
    return jsonify({"status": "Password changed successfully"})

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task status", "task_id": task_id, "status": "Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password', '')
    if password != admin_password:
        return jsonify({"status": "Access denied"}), 401
    new_setting = request.form.get('new_setting', '')
    if not isinstance(new_setting, str) or not new_setting.strip():
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400
    return jsonify({"status": "Setting applied", "new_setting": new_setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": f"Sample logs for task {task_id}"})

@app.route('/task/export', methods=['GET'])
def task_export():
    export_format = request.args.get('format', 'csv')
    if not _export_tasks_safely(export_format):
        return jsonify({"status": "Error", "message": "Unsupported export format"}), 400
    return jsonify({"status": "Task export started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    return jsonify({"status": "User profile", "profile": {"user_id": user_id, "name": "Jane Doe", "email": "jane.doe@example.com"}})

@app.route('/task/update', methods=['POST'])
def update_task():
    task_id = request.form.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    new_description = request.form.get('new_description', '')
    return jsonify({"status": "Task updated", "task_id": task_id, "new_description": new_description})

@app.route('/task/assign', methods=['POST'])
def assign_task():
    task_id = request.form.get('task_id')
    user_id = request.form.get('user_id')
    if not task_id or not user_id:
        return jsonify({"status": "Error", "message": "Task ID and User ID are required"}), 400
    return jsonify({"status": "Task assigned", "task_id": task_id, "user_id": user_id})

if __name__ == '__main__':
    app.run(debug=False)