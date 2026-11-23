import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

env_hash = os.getenv('ADMIN_PASSWORD_HASH')
if env_hash:
    ADMIN_PASSWORD_HASH = env_hash
else:
    ADMIN_PASSWORD_HASH = generate_password_hash('event_admin_2024')

SAFE_ARG_RE = re.compile(r'^[\w-]+$')


def is_safe_arg(value: str) -> bool:
    return bool(SAFE_ARG_RE.fullmatch(value))


@app.route('/event/add', methods=['POST'])
def add_event():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
        event_id = data.get('event_id')
        event_name = data.get('event_name')
        event_date = data.get('event_date')
        if not event_id or not event_name or not event_date:
            return jsonify({"status": "Error", "message": "Missing event information"}), 400
        return jsonify({"status": "Event added", "event_id": event_id, "event_name": event_name, "event_date": event_date})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/event/start', methods=['GET'])
def start_event():
    try:
        event_id = request.args.get('event_id')
        task = request.args.get('task')
        if not event_id or not task:
            return jsonify({"status": "Error", "message": "event_id and task are required"}), 400
        if not is_safe_arg(event_id) or not is_safe_arg(task):
            return jsonify({"status": "Error", "message": "Invalid characters in parameters"}), 400
        result = subprocess.run(['sh', 'start_event.sh', event_id, task], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({"status": "Error", "message": "Failed to start event", "details": result.stderr}), 500
        return jsonify({"status": "Event started"})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password and check_password_hash(ADMIN_PASSWORD_HASH, password):
        return jsonify({"status": "Login successful"})
    return jsonify({"status": "Login failed"}), 401


@app.route('/auth/update_password', methods=['POST'])
def update_password():
    global ADMIN_PASSWORD_HASH
    password = request.form.get('password')
    if not password or not check_password_hash(ADMIN_PASSWORD_HASH, password):
        return jsonify({"status": "Login failed"}), 401
    new_password = request.form.get('new_password')
    if not new_password or len(new_password) < 8:
        return jsonify({"status": "Error", "message": "Invalid new password (minimum 8 characters)"}), 400
    ADMIN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({"status": "Password updated"})


@app.route('/event/get', methods=['GET'])
def get_event():
    event_id = request.args.get('event_id')
    if not event_id:
        return jsonify({"status": "Error", "message": "Event ID is required"}), 400
    event = {"event_id": event_id, "event_name": "Sample Event", "event_date": "2024-01-01"}
    return jsonify({"status": "Event retrieved", "event": event})


@app.route('/event/remove', methods=['POST'])
def remove_event():
    event_id = request.form.get('event_id')
    if not event_id:
        return jsonify({"status": "Error", "message": "Event ID is required"}), 400
    return jsonify({"status": "Event removed", "event_id": event_id})


@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task status", "task_id": task_id, "status": "In Progress"})


@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password')
    if not password or not check_password_hash(ADMIN_PASSWORD_HASH, password):
        return jsonify({"status": "Login failed"}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400
    return jsonify({"status": "Setting updated", "setting": setting})


@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": f"Logs for task {task_id}"})


@app.route('/data/export', methods=['GET'])
def data_export():
    try:
        export_format = request.args.get('format', 'json').lower()
        if export_format not in ('json', 'csv'):
            return jsonify({"status": "Error", "message": "Unsupported export format"}), 400
        result = subprocess.run(['python', 'export_event_data.py', export_format], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({"status": "Error", "message": "Data export failed", "details": result.stderr}), 500
        return jsonify({"status": "Data export started"})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    user_info = {"user_id": user_id, "name": "John Doe", "email": "john.doe@example.com"}
    return jsonify({"status": "User information retrieved", "user_info": user_info})


if __name__ == "__main__":
    app.run(debug=False)