import os
import re
import hmac
import yaml
import subprocess
from flask import Flask, request, jsonify

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')
SAFE_TOKEN_RE = re.compile(r'^[a-zA-Z0-9_-]+$')

def _is_safe_token(value: str) -> bool:
    return bool(SAFE_TOKEN_RE.fullmatch(value))

def _constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1, val2)

app = Flask(__name__)

@app.route('/user/add', methods=['POST'])
def user_add():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    user_id = data.get('id')
    name = data.get('name')
    if not user_id or not name:
        return jsonify({'error': 'Missing id or name'}), 400
    return jsonify({'status': 'User added', 'id': user_id, 'name': name})

@app.route('/system/start_task', methods=['GET'])
def system_start_task():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if not task or not _is_safe_token(task):
        return jsonify({'error': 'Invalid task'}), 400
    if argument is not None and not _is_safe_token(argument):
        return jsonify({'error': 'Invalid argument'}), 400
    cmd = ['bash', 'start_task.sh', task]
    if argument is not None:
        cmd.append(argument)
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'error': 'Failed to start task'}), 500
    return jsonify({'status': 'Task started'})

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key', '')
    if _constant_time_compare(key, SECRET_KEY):
        return jsonify({'status': 'Authentication successful'})
    return jsonify({'status': 'Authentication failed'}), 401

@app.route('/admin/update_config', methods=['POST'])
def admin_update_config():
    key = request.form.get('key', '')
    if not _constant_time_compare(key, SECRET_KEY):
        return jsonify({'status': 'Authentication failed'}), 401
    new_config = request.form.get('new_config')
    if not new_config:
        return jsonify({'error': 'Missing new_config'}), 400
    return jsonify({'status': 'Configuration updated', 'new_config': new_config})

@app.route('/user/fetch', methods=['GET'])
def user_fetch():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'User fetched', 'user': {'id': user_id, 'name': 'Sample User'}})

@app.route('/user/delete', methods=['POST'])
def user_delete():
    user_id = request.form.get('id')
    if not user_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'User deleted', 'id': user_id})

@app.route('/admin/change_key', methods=['POST'])
def admin_change_key():
    return jsonify({'status': 'Error', 'message': 'Changing the secret key at runtime is not allowed'}), 403

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('id')
    if not task_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'Task status', 'id': task_id, 'status': 'Running'})

@app.route('/admin/set_preference', methods=['POST'])
def admin_set_preference():
    key = request.form.get('key', '')
    if not _constant_time_compare(key, SECRET_KEY):
        return jsonify({'status': 'Authentication failed'}), 401
    preference = request.form.get('preference')
    if not preference:
        return jsonify({'error': 'Missing preference'}), 400
    return jsonify({'status': 'Preference set', 'preference': preference})

@app.route('/logs/view', methods=['GET'])
def logs_view():
    log_id = request.args.get('id')
    if not log_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'Task logs', 'id': log_id, 'logs': f'Sample logs for task {log_id}'})

@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    if export_type not in ('json', 'csv', 'xml'):
        return jsonify({'error': 'Invalid export type'}), 400
    cmd = ['python3', 'export_data.py', export_type]
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'error': 'Failed to start export'}), 500
    return jsonify({'status': 'Data export started'})

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'User details', 'details': {'id': user_id, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'}})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if not task or not _is_safe_token(task):
        return jsonify({'error': 'Invalid task'}), 400
    if argument is not None and not _is_safe_token(argument):
        return jsonify({'error': 'Invalid argument'}), 400
    cmd = ['bash', 'execute_task.sh', task]
    if argument is not None:
        cmd.append(argument)
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'error': 'Failed to execute task'}), 500
    return jsonify({'status': 'Task execution started'})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('id')
    if not task_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'Task logs', 'id': task_id, 'logs': f'Sample logs for task {task_id}'})

if __name__ == '__main__':
    app.run(debug=False)