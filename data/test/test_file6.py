from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

ADMIN_PASSWORD = "admin1234"

@app.route('/task/create', methods=['POST'])
def create_task():
    yaml_task_data = request.data.decode('utf-8')
    try:
        task_info = yaml.load(yaml_task_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    task_id = task_info.get('task_id', '')
    task_description = task_info.get('task_description', '')

    if not task_id or not task_description:
        return jsonify({"status": "Error", "message": "Missing task information"}), 400

    return jsonify({"status": "Task created", "task_id": task_id, "task_description": task_description})

@app.route('/task/execute', methods=['GET'])
def execute_task():
    task_name = request.args.get('task_name', '')
    task_param = request.args.get('task_param', '')
    os.system(f"sh execute_task.sh {task_name} {task_param}")
    return jsonify({"status": "Task execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')

    if password == ADMIN_PASSWORD:
        return jsonify({"status": "Access granted"})
    else:
        return jsonify({"status": "Access denied"}), 401

@app.route('/admin/configure', methods=['POST'])
def configure_system():
    password = request.form.get('password', '')

    if password != ADMIN_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    
    new_config = request.form.get('new_config', '')
    if not new_config:
        return jsonify({"status": "Error", "message": "Invalid configuration"}), 400

    return jsonify({"status": "Configuration updated", "new_config": new_config})

@app.route('/task/retrieve', methods=['GET'])
def retrieve_task():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    task_info = {
        "task_id": task_id,
        "task_description": "Sample Task Description"
    }

    return jsonify({"status": "Task retrieved", "task_info": task_info})

@app.route('/task/delete', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    return jsonify({"status": "Task deleted", "task_id": task_id})

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')

    if old_password == ADMIN_PASSWORD:
        global ADMIN_PASSWORD
        ADMIN_PASSWORD = new_password
        return jsonify({"status": "Password changed successfully"})
    else:
        return jsonify({"status": "Access denied", "message": "Invalid old password"}), 401

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    return jsonify({"status": "Task status", "task_id": task_id, "status": "Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    
    new_setting = request.form.get('new_setting', '')
    if not new_setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400

    return jsonify({"status": "Setting applied", "new_setting": new_setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    logs = "Sample logs for task " + task_id

    return jsonify({"status": "Task logs", "task_id": task_id, "logs": logs})

@app.route('/task/export', methods=['GET'])
def export_tasks():
    export_format = request.args.get('format', 'csv')
    os.system(f"python3 export_tasks.py {export_format}")
    return jsonify({"status": "Task export started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    profile = {
        "user_id": user_id,
        "name": "Jane Doe",
        "email": "jane.doe@example.com"
    }

    return jsonify({"status": "User profile", "profile": profile})

@app.route('/task/update', methods=['POST'])
def update_task():
    task_id = request.form.get('task_id', '')
    new_description = request.form.get('new_description', '')

    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    return jsonify({"status": "Task updated", "task_id": task_id, "new_description": new_description})

@app.route('/task/assign', methods=['POST'])
def assign_task():
    task_id = request.form.get('task_id', '')
    user_id = request.form.get('user_id', '')

    if not task_id or not user_id:
        return jsonify({"status": "Error", "message": "Task ID and User ID are required"}), 400

    return jsonify({"status": "Task assigned", "task_id": task_id, "user_id": user_id})

app.run(debug=False)

