import os
import threading
import re
import subprocess
import yaml
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

admin_password_env = os.getenv('ADMIN_PASSWORD')
if not admin_password_env:
    raise RuntimeError('ADMIN_PASSWORD environment variable is required')
admin_password_hash = generate_password_hash(admin_password_env)
admin_lock = threading.Lock()
identifier_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
app = Flask(__name__)

def validate_identifier(value):
    return bool(value) and identifier_pattern.fullmatch(value)

def verify_admin(password):
    with admin_lock:
        return check_password_hash(admin_password_hash, password)

def update_admin_password(new_password):
    global admin_password_hash
    with admin_lock:
        admin_password_hash = generate_password_hash(new_password)

@app.route('/task/create', methods=['POST'])
def task_create():
    body = request.get_data(as_text=True)
    if not body:
        return jsonify(status='Error', message='Empty request body'), 400
    try:
        data = yaml.safe_load(body)
    except yaml.YAMLError:
        return jsonify(status='Error', message='Invalid YAML format'), 400
    if not isinstance(data, dict):
        return jsonify(status='Error', message='YAML must represent an object'), 400
    task_id = data.get('task_id')
    task_description = data.get('task_description')
    if not task_id or not task_description:
        return jsonify(status='Error', message='Missing task information'), 400
    return jsonify(status='Task created', task_id=task_id, task_description=task_description)

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task_name = request.args.get('task_name')
    task_param = request.args.get('task_param')
    if not validate_identifier(task_name):
        return jsonify(status='Error', message='Invalid or missing task_name'), 400
    if not validate_identifier(task_param):
        return jsonify(status='Error', message='Invalid or missing task_param'), 400
    try:
        subprocess.run(['sh', 'execute_task.sh', task_name, task_param], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return jsonify(status='Error', message='Task execution failed', details=e.stderr), 500
    return jsonify(status='Task execution started')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if verify_admin(password):
        return jsonify(status='Access granted')
    return jsonify(status='Access denied'), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    if not verify_admin(password):
        return jsonify(status='Access denied'), 401
    new_config = request.form.get('new_config')
    if new_config is None:
        return jsonify(status='Error', message='Invalid configuration'), 400
    return jsonify(status='Configuration updated', new_config=new_config)

@app.route('/task/retrieve', methods=['GET'])
def task_retrieve():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    task_info = {'task_id': task_id, 'task_description': 'Sample Task Description'}
    return jsonify(status='Task retrieved', task_info=task_info)

@app.route('/task/delete', methods=['POST'])
def task_delete():
    task_id = request.form.get('task_id')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    return jsonify(status='Task deleted', task_id=task_id)

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    if not new_password:
        return jsonify(status='Error', message='New password must be provided'), 400
    if not verify_admin(old_password):
        return jsonify(status='Access denied', message='Invalid old password'), 401
    update_admin_password(new_password)
    return jsonify(status='Password changed successfully')

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    return jsonify(status='Task status', task_id=task_id, task_state='Running')

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password', '')
    if not verify_admin(password):
        return jsonify(status='Access denied'), 401
    new_setting = request.form.get('new_setting')
    if new_setting is None:
        return jsonify(status='Error', message='Invalid setting'), 400
    return jsonify(status='Setting applied', new_setting=new_setting)

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    logs = f'Sample logs for task {task_id}'
    return jsonify(status='Task logs', task_id=task_id, logs=logs)

@app.route('/task/export', methods=['GET'])
def task_export():
    fmt = request.args.get('format', 'csv').lower()
    if fmt not in {'csv', 'json', 'xml'}:
        return jsonify(status='Error', message='Unsupported export format'), 400
    try:
        subprocess.run(['python3', 'export_tasks.py', fmt], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return jsonify(status='Error', message='Export failed', details=e.stderr), 500
    return jsonify(status='Task export started')

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(status='Error', message='User ID is required'), 400
    profile = {'user_id': user_id, 'name': 'Jane Doe', 'email': 'jane.doe@example.com'}
    return jsonify(status='User profile', profile=profile)

@app.route('/task/update', methods=['POST'])
def task_update():
    task_id = request.form.get('task_id')
    new_description = request.form.get('new_description')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    return jsonify(status='Task updated', task_id=task_id, new_description=new_description)

@app.route('/task/assign', methods=['POST'])
def task_assign():
    task_id = request.form.get('task_id')
    user_id = request.form.get('user_id')
    if not task_id or not user_id:
        return jsonify(status='Error', message='Task ID and User ID are required'), 400
    return jsonify(status='Task assigned', task_id=task_id, user_id=user_id)

if __name__ == '__main__':
    app.run(debug=False)