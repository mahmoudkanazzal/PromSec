import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

secret_token = os.getenv('SECRET_TOKEN', 'default_secure_token_12345')
safe_pattern = re.compile(r'^[A-Za-z0-9_-]+$')


def is_safe_input(value: str) -> bool:
    return bool(safe_pattern.fullmatch(value))


@app.route('/config/upload', methods=['POST'])
def upload_config():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'YAML must be a mapping'}), 400
    config_name = data.get('config_name')
    config_value = data.get('config_value')
    if not config_name or not config_value:
        return jsonify({'error': 'config_name and config_value are required'}), 400
    return jsonify({
        'status': 'Configuration uploaded',
        'config_name': config_name,
        'config_value': config_value
    })


@app.route('/task/execute', methods=['GET'])
def execute_task():
    task = request.args.get('task')
    param = request.args.get('param')
    if not task or not param:
        return jsonify({'error': 'task and param are required'}), 400
    if not is_safe_input(task) or not is_safe_input(param):
        return jsonify({'error': 'Invalid characters in task or param'}), 400
    try:
        subprocess.run(['sh', 'execute_task.sh', task, param],
                       check=False,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'error': 'Failed to start task'}), 500
    return jsonify({'status': 'Task execution started'})


@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    token = request.form.get('token')
    if token == secret_token:
        return jsonify({'status': 'Verification successful'})
    return jsonify({'status': 'Verification failed'}), 401


@app.route('/admin/update_token', methods=['POST'])
def update_token():
    global secret_token
    current = request.form.get('current_token')
    new = request.form.get('new_token')
    if current != secret_token:
        return jsonify({'status': 'Verification failed'}), 401
    if not new:
        return jsonify({'error': 'new_token cannot be empty'}), 400
    secret_token = new
    return jsonify({'status': 'Token updated'})


@app.route('/config/retrieve', methods=['GET'])
def retrieve_config():
    name = request.args.get('config_name')
    if not name:
        return jsonify({'error': 'config_name is required'}), 400
    return jsonify({
        'status': 'Configuration retrieved',
        'config': {
            'config_name': name,
            'config_value': 'Example Config Value'
        }
    })


@app.route('/config/delete', methods=['POST'])
def delete_config():
    name = request.form.get('config_name')
    if not name:
        return jsonify({'error': 'config_name is required'}), 400
    return jsonify({
        'status': 'Configuration deleted',
        'config_name': name
    })


@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'task_id is required'}), 400
    return jsonify({
        'status': 'Task status',
        'task_id': task_id,
        'status_detail': 'Running'
    })


@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    token = request.form.get('token')
    if token != secret_token:
        return jsonify({'status': 'Access denied'}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({'error': 'setting is required'}), 400
    return jsonify({
        'status': 'Setting updated',
        'setting': setting
    })


@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'task_id is required'}), 400
    return jsonify({
        'status': 'Task logs',
        'task_id': task_id,
        'logs': f'Logs for task {task_id}'
    })


@app.route('/backup/data', methods=['GET'])
def backup_data():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ('json', 'csv'):
        return jsonify({'error': 'Unsupported format'}), 400
    try:
        subprocess.run(['python3', 'backup_data.py', fmt],
                       check=False,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'error': 'Backup failed'}), 500
    return jsonify({'status': 'Data backup started'})


@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    return jsonify({
        'status': 'User profile retrieved',
        'profile': {
            'user_id': user_id,
            'name': 'Michael Brown',
            'email': 'michael.brown@example.com'
        }
    })


if __name__ == '__main__':
    app.run(debug=False)