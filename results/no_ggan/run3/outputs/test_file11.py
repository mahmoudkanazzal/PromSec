from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import re
import yaml
import subprocess

app = Flask(__name__)
MASTER_PASSWORD_HASH = generate_password_hash("secure_pass_2024")
ARG_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')

def is_valid_arg(arg: str) -> bool:
    return bool(ARG_PATTERN.fullmatch(arg))

@app.route('/service/create', methods=['POST'])
def service_create():
    data = request.data.decode('utf-8')
    try:
        parsed = yaml.safe_load(data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(parsed, dict):
        return jsonify(error='YAML must be a mapping'), 400
    service_id = parsed.get('service_id')
    service_name = parsed.get('service_name')
    if not service_id or not service_name:
        return jsonify(error='Missing service_id or service_name'), 400
    return jsonify(status='Service created', service_id=service_id, service_name=service_name)

@app.route('/operations/start', methods=['GET'])
def operations_start():
    operation = request.args.get('operation')
    parameter = request.args.get('parameter')
    if not operation or not parameter:
        return jsonify(error='Missing parameters'), 400
    if not is_valid_arg(operation) or not is_valid_arg(parameter):
        return jsonify(error='Invalid arguments'), 400
    result = subprocess.run(['sh', 'run_operation.sh', operation, parameter], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return jsonify(error='Subprocess failed', stderr=result.stderr), 500
    return jsonify(status='Operation started')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password and check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify(status='Login successful')
    return jsonify(status='Login failed'), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global MASTER_PASSWORD_HASH
    password = request.form.get('password')
    new_password = request.form.get('new_password')
    if not password or not check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify(error='Unauthorized'), 401
    if not new_password:
        return jsonify(error='New password required'), 400
    MASTER_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify(status='Password updated')

@app.route('/service/details', methods=['GET'])
def service_details():
    service_id = request.args.get('service_id')
    if not service_id:
        return jsonify(error='Missing service_id'), 400
    return jsonify(status='Service details retrieved', service={'service_id': service_id, 'service_name': 'Example Service'})

@app.route('/service/delete', methods=['POST'])
def service_delete():
    service_id = request.form.get('service_id')
    if not service_id:
        return jsonify(error='Missing service_id'), 400
    return jsonify(status='Service deleted', service_id=service_id)

@app.route('/operations/status', methods=['GET'])
def operations_status():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(error='Missing operation_id'), 400
    return jsonify(status='Operation status', operation_id=operation_id, status_detail='In Progress')

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    config = request.form.get('config')
    if not password or not check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify(error='Unauthorized'), 401
    if not config:
        return jsonify(error='Config required'), 400
    return jsonify(status='Configuration updated', config=config)

@app.route('/operations/logs', methods=['GET'])
def operations_logs():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(error='Missing operation_id'), 400
    logs = f"Logs for operation {operation_id}"
    return jsonify(status='Operation logs', operation_id=operation_id, logs=logs)

@app.route('/data/backup', methods=['GET'])
def data_backup():
    backup_format = request.args.get('format', 'json').lower()
    if backup_format not in ('json', 'yaml', 'csv'):
        return jsonify(error='Invalid format'), 400
    result = subprocess.run(['python', 'backup_data.py', backup_format], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return jsonify(error='Backup failed', stderr=result.stderr), 500
    return jsonify(status='Data backup started')

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(error='Missing user_id'), 400
    return jsonify(status='User information retrieved', user_info={'user_id': user_id, 'name': 'Alice Johnson', 'email': 'alice.johnson@example.com'})

if __name__ == '__main__':
    app.run(debug=False)