import os
import subprocess
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

secret_token = os.getenv('SECRET_TOKEN', 'secure_token_2024')


@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    config_name = data.get('config_name')
    config_value = data.get('config_value')
    if not config_name or not config_value:
        return jsonify({"status": "Error", "message": "Missing configuration details"}), 400
    return jsonify({"status": "Configuration uploaded", "config_name": config_name, "config_value": config_value}), 200


@app.route('/task/execute', methods=['GET'])
def execute_task():
    task = request.args.get('task', '')
    param = request.args.get('param', '')
    subprocess.run(['sh', 'execute_task.sh', task, param], check=False, capture_output=True, text=True)
    return jsonify({"status": "Task execution started"}), 200


@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    token = request.form.get('token', '')
    if token == secret_token:
        return jsonify({"status": "Verification successful"}), 200
    return jsonify({"status": "Verification failed"}), 401


@app.route('/admin/update_token', methods=['POST'])
def update_token():
    global secret_token
    current = request.form.get('current_token', '')
    new = request.form.get('new_token', '')
    if current != secret_token:
        return jsonify({"status": "Verification failed"}), 401
    if not new:
        return jsonify({"status": "Error", "message": "Invalid new token"}), 400
    secret_token = new
    return jsonify({"status": "Token updated"}), 200


@app.route('/config/retrieve', methods=['GET'])
def retrieve_config():
    name = request.args.get('config_name', '')
    if not name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400
    return jsonify({"status": "Configuration retrieved", "config": {"config_name": name, "config_value": "Example Config Value"}}), 200


@app.route('/config/delete', methods=['POST'])
def delete_config():
    name = request.form.get('config_name', '')
    if not name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400
    return jsonify({"status": "Configuration deleted", "config_name": name}), 200


@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task status", "task_id": task_id, "status": "Running"}), 200


@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    token = request.form.get('token', '')
    setting = request.form.get('setting', '')
    if token != secret_token:
        return jsonify({"status": "Access denied"}), 401
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400
    return jsonify({"status": "Setting updated", "setting": setting}), 200


@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": f"Logs for task {task_id}"}), 200


@app.route('/backup/data', methods=['GET'])
def backup_data():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ('json', 'yaml'):
        return jsonify({"status": "Error", "message": "Unsupported backup format"}), 400
    subprocess.run(['python3', 'backup_data.py', fmt], check=False, capture_output=True, text=True)
    return jsonify({"status": "Data backup started"}), 200


@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    profile = {"user_id": user_id, "name": "Michael Brown", "email": "michael.brown@example.com"}
    return jsonify({"status": "User profile retrieved", "profile": profile}), 200


if __name__ == '__main__':
    app.run(debug=False)