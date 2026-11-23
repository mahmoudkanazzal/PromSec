from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import threading
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
MASTER_PASSWORD_HASH = generate_password_hash("secure_pass_2024")
_password_lock = threading.Lock()
ALLOWED_OPERATIONS = {"start", "stop", "restart"}
ALLOWED_BACKUP_FORMATS = {"json", "sql"}

def _run_script(script_path, *args):
    try:
        subprocess.run([script_path, *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

@app.route('/service/create', methods=['POST'])
def service_create():
    try:
        data = request.data.decode('utf-8')
        payload = yaml.safe_load(data)
    except Exception:
        return jsonify(error="Invalid YAML"), 400
    if not isinstance(payload, dict):
        return jsonify(error="YAML must be a mapping"), 400
    service_id = payload.get('service_id')
    service_name = payload.get('service_name')
    if not service_id or not service_name:
        return jsonify(error="Missing service_id or service_name"), 400
    return jsonify(status="Service created", service_id=service_id, service_name=service_name)

@app.route('/operations/start', methods=['GET'])
def operations_start():
    operation = request.args.get('operation', '').strip()
    parameter = request.args.get('parameter', '').strip()
    if operation not in ALLOWED_OPERATIONS:
        return jsonify(error="Invalid operation"), 400
    if not all(c.isalnum() or c in '-_.' for c in parameter):
        return jsonify(error="Invalid parameter"), 400
    _run_script("./run_operation.sh", operation, parameter)
    return jsonify(status="Operation started")

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify(message="Login successful")
    return jsonify(message="Login failed"), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global MASTER_PASSWORD_HASH
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify(message="Invalid current password"), 401
    if len(new_password) < 8:
        return jsonify(error="New password must be at least 8 characters"), 400
    with _password_lock:
        MASTER_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify(message="Password updated")

@app.route('/service/details', methods=['GET'])
def service_details():
    service_id = request.args.get('service_id')
    if not service_id:
        return jsonify(error="Missing service_id"), 400
    return jsonify(status="Service details retrieved", service={"service_id": service_id, "service_name": "Example Service"})

@app.route('/service/delete', methods=['POST'])
def service_delete():
    service_id = request.form.get('service_id')
    if not service_id:
        return jsonify(error="Missing service_id"), 400
    return jsonify(status="Service deleted", service_id=service_id)

@app.route('/operations/status', methods=['GET'])
def operations_status():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(error="Missing operation_id"), 400
    return jsonify(status="Operation status", operation_id=operation_id, state="In Progress")

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    config = request.form.get('config', '')
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify(message="Access denied"), 401
    if not config:
        return jsonify(error="Config cannot be empty"), 400
    return jsonify(message="Configuration updated", config=config)

@app.route('/operations/logs', methods=['GET'])
def operations_logs():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(error="Missing operation_id"), 400
    return jsonify(status="Operation logs", operation_id=operation_id, logs=f"Logs for operation {operation_id}")

@app.route('/data/backup', methods=['GET'])
def data_backup():
    backup_format = request.args.get('format', 'json').strip().lower()
    if backup_format not in ALLOWED_BACKUP_FORMATS:
        return jsonify(error="Invalid backup format"), 400
    _run_script("python", "backup_data.py", backup_format)
    return jsonify(message="Data backup started")

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(error="Missing user_id"), 400
    return jsonify(status="User information retrieved", user={"user_id": user_id, "name": "Alice Johnson", "email": "alice.johnson@example.com"})

if __name__ == "__main__":
    app.run(debug=False)