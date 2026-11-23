import os
import subprocess
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

master_password = os.getenv('MASTER_PASSWORD', 'ChangeMe!StrongPassword123')


@app.route('/service/create', methods=['POST'])
def service_create():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify(status='Error', message='Invalid YAML format'), 400
    if not isinstance(data, dict):
        return jsonify(status='Error', message='Invalid YAML format'), 400
    service_id = data.get('service_id')
    service_name = data.get('service_name')
    if not service_id or not service_name:
        return jsonify(status='Error', message='Missing service information'), 400
    return jsonify(status='Service created', service_id=service_id, service_name=service_name)


@app.route('/operations/start', methods=['GET'])
def operations_start():
    operation = request.args.get('operation')
    parameter = request.args.get('parameter')
    if not operation:
        return jsonify(status='Error', message='Operation name is required'), 400
    args = ['sh', 'run_operation.sh', operation]
    if parameter:
        args.append(parameter)
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
    except Exception as e:
        return jsonify(status='Error', message=f'Failed to start operation: {e}'), 500
    if result.returncode != 0:
        return jsonify(status='Error', message='Operation script returned an error', stderr=result.stderr), 500
    return jsonify(status='Operation started', stdout=result.stdout)


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == master_password:
        return jsonify(status='Login successful')
    return jsonify(status='Login failed'), 401


@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global master_password
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if password != master_password:
        return jsonify(status='Login failed'), 401
    if not new_password:
        return jsonify(status='Error', message='Invalid new password'), 400
    master_password = new_password
    return jsonify(status='Password updated')


@app.route('/service/details', methods=['GET'])
def service_details():
    service_id = request.args.get('service_id')
    if not service_id:
        return jsonify(status='Error', message='Service ID is required'), 400
    return jsonify(status='Service details retrieved', service_id=service_id, service_name='Example Service')


@app.route('/service/delete', methods=['POST'])
def service_delete():
    service_id = request.form.get('service_id')
    if not service_id:
        return jsonify(status='Error', message='Service ID is required'), 400
    return jsonify(status='Service deleted', service_id=service_id)


@app.route('/operations/status', methods=['GET'])
def operations_status():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(status='Error', message='Operation ID is required'), 400
    return jsonify(status='Operation status', operation_id=operation_id, operation_state='In Progress')


@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    config = request.form.get('config', '')
    if password != master_password:
        return jsonify(status='Access denied'), 401
    if not config:
        return jsonify(status='Error', message='Invalid configuration'), 400
    return jsonify(status='Configuration updated', config=config)


@app.route('/operations/logs', methods=['GET'])
def operations_logs():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify(status='Error', message='Operation ID is required'), 400
    log = f'Logs for operation {operation_id}'
    return jsonify(status='Operation logs', logs=log)


@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ('json', 'yaml'):
        return jsonify(status='Error', message=f'Unsupported backup format: {fmt}'), 400
    args = ['python', 'backup_data.py', fmt]
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
    except Exception as e:
        return jsonify(status='Error', message=f'Failed to start backup: {e}'), 500
    if result.returncode != 0:
        return jsonify(status='Error', message='Backup script returned an error', stderr=result.stderr), 500
    return jsonify(status='Data backup started', stdout=result.stdout)


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(status='Error', message='User ID is required'), 400
    return jsonify(status='User information retrieved', user_id=user_id, name='Alice Johnson', email='alice.johnson@example.com')


if __name__ == '__main__':
    app.run(debug=False)