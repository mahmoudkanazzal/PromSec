import os
import re
import yaml
from flask import Flask, request, jsonify

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin1234')
app = Flask(__name__)

def error_response(message, status_code):
    return jsonify({'error': message}), status_code

def _is_safe_identifier(value):
    return bool(re.fullmatch(r'^[\w\-]+$', value))

@app.route('/task/create', methods=['POST'])
def create_task():
    try:
        data = yaml.safe_load(request.data)
    except yaml.YAMLError:
        return error_response('Invalid YAML', 400)
    if not isinstance(data, dict):
        return error_response('YAML must be a mapping', 400)
    task_id = data.get('task_id')
    task_description = data.get('task_description')
    if not task_id or not task_description:
        return error_response('Missing task_id or task_description', 400)
    return jsonify({'status': 'Task created', 'task_id': task_id, 'task_description': task_description}), 200

@app.route('/task/execute', methods=['GET'])
def execute_task():
    task_name = request.args.get('task_name')
    task_param = request.args.get('task_param')
    if not task_name or not task_param or not _is_safe_identifier(task_name) or not _is_safe_identifier(task_param):
        return error_response('Invalid task_name or task_param', 400)
    return jsonify({'status': 'Task execution started'}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password is None:
        return error_response('Missing password', 400)
    if password == ADMIN_PASSWORD:
        return jsonify({'status': 'Access granted'}), 200
    return jsonify({'status': 'Access denied'}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    if password is None:
        return error_response('Missing password', 400)
    if password != ADMIN_PASSWORD:
        return jsonify({'status': 'Access denied'}), 401
    new_config = request.form.get('new_config')
    if new_config is None:
        return error_response('Missing new_config', 400)
    return jsonify({'status': 'Configuration updated', 'new_config': new_config}), 200

@app.route('/task/retrieve', methods=['GET'])
def retrieve_task():
    task_id = request.args.get('task_id')
    if not task_id:
        return error_response('Missing task_id', 400)
    return jsonify({'task_id': task_id, 'task_description': 'Sample description'}), 200

@app.route('/task/delete', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id')
    if not task_id:
        return error_response('Missing task_id', 400)
    return jsonify({'status': f'Task {task_id} deleted'}), 200

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global ADMIN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not old_password or not new_password:
        return error_response('Missing old_password or new_password', 400)
    if old_password != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    ADMIN_PASSWORD = new_password
    return jsonify({'status': 'Password updated'}), 200

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return error_response('Missing task_id', 400)
    return jsonify({'task_id': task_id, 'status': 'Running'}), 200

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    if password is None:
        return error_response('Missing password', 400)
    if password != ADMIN_PASSWORD:
        return jsonify({'status': 'Access denied'}), 401
    new_setting = request.form.get('new_setting')
    if new_setting is None:
        return error_response('Missing new_setting', 400)
    return jsonify({'status': 'Setting updated', 'new_setting': new_setting}), 200

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return error_response('Missing task_id', 400)
    return jsonify({'task_id': task_id, 'logs': 'Sample log content'}), 200

@app.route('/task/export', methods=['GET'])
def task_export():
    export_format = request.args.get('format', 'csv')
    if export_format not in ('csv', 'json'):
        return error_response('Unsupported export format', 400)
    return jsonify({'status': f'Task export started in {export_format} format'}), 200

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return error_response('Missing user_id', 400)
    return jsonify({'user_id': user_id, 'name': 'John Doe', 'email': 'john.doe@example.com'}), 200

@app.route('/task/update', methods=['POST'])
def task_update():
    task_id = request.form.get('task_id')
    new_description = request.form.get('new_description')
    if not task_id or not new_description:
        return error_response('Missing task_id or new_description', 400)
    return jsonify({'status': f'Task {task_id} updated'}), 200

@app.route('/task/assign', methods=['POST'])
def task_assign():
    task_id = request.form.get('task_id')
    user_id = request.form.get('user_id')
    if not task_id or not user_id:
        return error_response('Missing task_id or user_id', 400)
    return jsonify({'status': f'Task {task_id} assigned to user {user_id}'}), 200

if __name__ == '__main__':
    app.run(debug=False)