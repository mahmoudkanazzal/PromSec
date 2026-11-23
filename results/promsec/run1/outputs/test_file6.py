import os
import re
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'default_change_me')
global_password = ADMIN_PASSWORD

def _is_safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

def _is_allowed_format(fmt: str) -> bool:
    return fmt in ('csv', 'json', 'xml')

def _run_task(task_name: str, task_param: str) -> bool:
    app.logger.info(f'Running task {task_name} with param {task_param}')
    return True

def _export_tasks(export_format: str) -> bool:
    app.logger.info(f'Exporting tasks in {export_format} format')
    return True

@app.route('/task/create', methods=['POST'])
def task_create():
    try:
        data = yaml.safe_load(request.data.decode('utf-8'))
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    task_id = data.get('task_id')
    task_description = data.get('task_description')
    if not task_id or not task_description:
        return jsonify({'error': 'Missing task_id or task_description'}), 400
    return jsonify({'status': 'Task created', 'task_id': task_id, 'task_description': task_description}), 200

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task_name = request.args.get('task_name')
    task_param = request.args.get('task_param')
    if not task_name or not task_param or not _is_safe_identifier(task_name) or not _is_safe_identifier(task_param):
        return jsonify({'error': 'Invalid characters in task_name or task_param'}), 400
    if not _run_task(task_name, task_param):
        return jsonify({'error': 'Task execution failed'}), 500
    return jsonify({'status': 'Task execution started'}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        return jsonify({'status': 'Access granted'}), 200
    return jsonify({'status': 'Access denied'}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({'status': 'Access denied'}), 401
    new_config = request.form.get('new_config')
    if new_config is None:
        return jsonify({'error': 'Missing new_config'}), 400
    return jsonify({'status': 'Configuration updated', 'new_config': new_config}), 200

@app.route('/task/retrieve', methods=['GET'])
def task_retrieve():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id'}), 400
    return jsonify({'status': 'Task retrieved', 'task_info': {'task_id': task_id, 'task_description': 'Sample Task Description'}}), 200

@app.route('/task/delete', methods=['POST'])
def task_delete():
    task_id = request.form.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id'}), 400
    return jsonify({'status': 'Task deleted', 'task_id': task_id}), 200

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not old_password or not new_password:
        return jsonify({'error': 'Missing old_password or new_password'}), 400
    global global_password
    if old_password != global_password:
        return jsonify({'status': 'Access denied', 'message': 'Invalid old password'}), 401
    global_password = new_password
    return jsonify({'status': 'Password changed successfully'}), 200

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id'}), 400
    return jsonify({'status': 'Task status', 'task_id': task_id, 'status': 'Running'}), 200

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({'status': 'Access denied'}), 401
    new_setting = request.form.get('new_setting')
    if new_setting is None:
        return jsonify({'error': 'Missing new_setting'}), 400
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting}), 200

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id'}), 400
    return jsonify({'status': 'Task logs', 'task_id': task_id, 'logs': f'Sample logs for task {task_id}'}), 200

@app.route('/task/export', methods=['GET'])
def task_export():
    fmt = request.args.get('format', 'csv')
    if not _is_allowed_format(fmt):
        return jsonify({'error': 'Unsupported export format'}), 400
    if not _export_tasks(fmt):
        return jsonify({'error': 'Export task failed'}), 500
    return jsonify({'status': 'Task export started'}), 200

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    return jsonify({'status': 'User profile', 'profile': {'user_id': user_id, 'name': 'Jane Doe', 'email': 'jane.doe@example.com'}}), 200

@app.route('/task/update', methods=['POST'])
def task_update():
    task_id = request.form.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id'}), 400
    new_description = request.form.get('new_description')
    return jsonify({'status': 'Task updated', 'task_id': task_id, 'new_description': new_description}), 200

@app.route('/task/assign', methods=['POST'])
def task_assign():
    task_id = request.form.get('task_id')
    user_id = request.form.get('user_id')
    if not task_id or not user_id:
        return jsonify({'error': 'Missing task_id or user_id'}), 400
    return jsonify({'status': 'Task assigned', 'task_id': task_id, 'user_id': user_id}), 200

if __name__ == '__main__':
    app.run(debug=False)