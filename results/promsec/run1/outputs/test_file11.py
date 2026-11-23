import os
import re
import subprocess
from flask import Flask, request, jsonify
import yaml

# Load master password from environment; raise if missing
_master_password = os.getenv('MASTER_PASSWORD')
if not _master_password:
    raise RuntimeError('MASTER_PASSWORD environment variable not set')

app = Flask(__name__)

def _is_safe_token(token: str) -> bool:
    """Validate token against safe pattern to prevent injection."""
    return bool(re.fullmatch(r'[\w\-.]+', token))

@app.route('/service/create', methods=['POST'])
def create_service():
    try:
        raw = request.get_data(as_text=True)  # Read raw body as text
        data = yaml.safe_load(raw)  # Use safe_load to avoid arbitrary code execution
    except yaml.YAMLError:
        return jsonify(status='Error', message='Invalid YAML format'), 400

    service_id = data.get('service_id') if isinstance(data, dict) else None
    service_name = data.get('service_name') if isinstance(data, dict) else None

    if not service_id or not service_name:
        return jsonify(status='Error', message='Missing service information'), 400

    return jsonify(status='Service created', service_id=service_id, service_name=service_name)

@app.route('/operations/start', methods=['GET'])
def start_operation():
    operation = request.args.get('operation')
    parameter = request.args.get('parameter')

    if not operation or not parameter or not _is_safe_token(operation) or not _is_safe_token(parameter):
        return jsonify(status='Error', message='Invalid operation or parameter'), 400

    try:
        # Use check=True to raise CalledProcessError on non-zero exit
        subprocess.run(['sh', 'run_operation.sh', operation, parameter], check=True)
    except subprocess.CalledProcessError:
        return jsonify(status='Error', message='Failed to start operation'), 500

    return jsonify(status='Operation started')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == _master_password:
        return jsonify(status='Login successful')
    return jsonify(status='Login failed'), 401

@app.route('/admin/update_password', methods=['POST'])
def update_password():
    global _master_password
    current = request.form.get('password', '')
    if current != _master_password:
        return jsonify(status='Login failed'), 401

    new_password = request.form.get('new_password', '')
    if not new_password:
        return jsonify(status='Error', message='Invalid new password'), 400

    _master_password = new_password
    return jsonify(status='Password updated')

@app.route('/service/details', methods=['GET'])
def service_details():
    service_id = request.args.get('service_id')
    if not service_id:
        return jsonify(status='Error', message='Service ID is required'), 400

    service = {'service_id': service_id, 'service_name': 'Example Service'}
    return jsonify(status='Service details retrieved', service=service)

@app.route('/service/delete', methods=['POST'])
def delete_service():
    service_id = request.form.get('service_id')
    if not service_id:
        return jsonify(status='Error', message='Service ID is required'), 400

    return jsonify(status='Service deleted', service_id=service_id)

@app.route('/operations/status', methods=['GET'])
def operation_status():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(status='Error', message='Operation ID is required'), 400

    # Use a distinct key for the operation's state to avoid duplicate 'status' field
    return jsonify(status='Operation status', operation_id=operation_id, operation_state='In Progress')

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    if password != _master_password:
        return jsonify(status='Access denied'), 401

    config = request.form.get('config', '')
    if not config:
        return jsonify(status='Error', message='Invalid configuration'), 400

    return jsonify(status='Configuration updated', config=config)

@app.route('/operations/logs', methods=['GET'])
def operation_logs():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(status='Error', message='Operation ID is required'), 400

    logs = f'Logs for operation {operation_id}'
    return jsonify(status='Operation logs', operation_id=operation_id, logs=logs)

@app.route('/data/backup', methods=['GET'])
def data_backup():
    backup_format = request.args.get('format', 'json')
    if backup_format not in ('json', 'yaml', 'csv'):
        return jsonify(status='Error', message='Unsupported backup format'), 400

    try:
        # Run backup script safely; check=True raises on failure
        subprocess.run(['python', 'backup_data.py', backup_format], check=True)
    except subprocess.CalledProcessError:
        return jsonify(status='Error', message='Backup process failed'), 500

    return jsonify(status='Data backup started')

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(status='Error', message='User ID is required'), 400

    user = {
        'user_id': user_id,
        'name': 'Alice Johnson',
        'email': 'alice.johnson@example.com'
    }
    return jsonify(status='User information retrieved', user_info=user)

if __name__ == '__main__':
    app.run(debug=False)