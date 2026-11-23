import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

MASTER_PASSWORD_HASH = os.getenv('MASTER_PASSWORD_HASH')
if not MASTER_PASSWORD_HASH:
    MASTER_PASSWORD_HASH = generate_password_hash('secure_pass_2024')

def _is_safe_token(token: str) -> bool:
    return bool(re.fullmatch(r'^[\w\-]+$', token))

def _is_allowed_format(fmt: str) -> bool:
    return fmt.lower() in ('json', 'yaml', 'yml')

@app.route('/service/create', methods=['POST'])
def service_create():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        return jsonify({'error': 'Invalid YAML payload'}), 400
    service_id = data.get('service_id')
    service_name = data.get('service_name')
    if not service_id or not service_name:
        return jsonify({'error': 'Missing service_id or service_name'}), 400
    return jsonify({'status': 'Service created', 'service_id': service_id, 'service_name': service_name})

@app.route('/operations/start', methods=['GET'])
def operations_start():
    operation = request.args.get('operation', '')
    parameter = request.args.get('parameter', '')
    if not _is_safe_token(operation) or not _is_safe_token(parameter):
        return jsonify({'error': 'Invalid parameters'}), 400
    subprocess.run(['sh', 'run_operation.sh', operation, parameter], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify({'status': 'Operation started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify({'status': 'Login successful'})
    return jsonify({'status': 'Login failed'}), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global MASTER_PASSWORD_HASH
    password = request.form.get('password', '')
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify({'status': 'Login failed'}), 401
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({'error': 'Missing new_password'}), 400
    MASTER_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'status': 'Password updated'})

@app.route('/service/details', methods=['GET'])
def service_details():
    service_id = request.args.get('service_id')
    if not service_id:
        return jsonify({'error': 'Missing service_id'}), 400
    return jsonify({'status': 'Service details retrieved', 'service': {'service_id': service_id, 'service_name': 'Example Service'}})

@app.route('/service/delete', methods=['POST'])
def service_delete():
    service_id = request.form.get('service_id')
    if not service_id:
        return jsonify({'error': 'Missing service_id'}), 400
    return jsonify({'status': 'Service deleted', 'service_id': service_id})

@app.route('/operations/status', methods=['GET'])
def operations_status():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify({'error': 'Missing operation_id'}), 400
    return jsonify({'status': 'Operation status', 'operation_id': operation_id, 'status_detail': 'In Progress'})

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify({'status': 'Login failed'}), 401
    config = request.form.get('config')
    if config is None:
        return jsonify({'error': 'Missing config'}), 400
    return jsonify({'status': 'Configuration updated', 'config': config})

@app.route('/operations/logs', methods=['GET'])
def operations_logs():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify({'error': 'Missing operation_id'}), 400
    logs = f'Logs for operation {operation_id}'
    return jsonify({'status': 'Operation logs', 'operation_id': operation_id, 'logs': logs})

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    if not _is_allowed_format(fmt):
        return jsonify({'error': 'Invalid format'}), 400
    backup_format = fmt.lower()
    subprocess.run(['python', 'backup_data.py', backup_format], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return jsonify({'status': 'Data backup started'})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    return jsonify({'status': 'User information retrieved', 'user_info': {'user_id': user_id, 'name': 'Alice Johnson', 'email': 'alice.johnson@example.com'}})

if __name__ == '__main__':
    app.run(debug=False)