import os
import re
import yaml
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
admin_password = os.getenv('ADMIN_PASSWORD', 'default_admin_password')
app.config['ADMIN_PASSWORD'] = admin_password

def get_json_error(message, status_code=400):
    return make_response(jsonify({'error': message}), status_code)

def _run_task_script(task, parameter):
    allowed_tasks = {'backup', 'cleanup', 'report'}
    if task not in allowed_tasks:
        raise ValueError('Task not allowed')
    return f"Task {task} executed with parameter {parameter}"

def _export_data(fmt):
    return f"Data exported in {fmt} format"

@app.route('/data/upload', methods=['POST'])
def data_upload():
    raw = request.get_data(as_text=True)
    try:
        parsed = yaml.safe_load(raw)
    except Exception:
        return get_json_error('Invalid YAML')
    if not isinstance(parsed, dict):
        return get_json_error('YAML must be a mapping')
    data_id = parsed.get('data_id')
    data_value = parsed.get('data_value')
    if data_id is None or data_value is None:
        return get_json_error('Missing data_id or data_value')
    return jsonify({'status': 'Data uploaded', 'data_id': data_id, 'data_value': data_value})

@app.route('/task/execute')
def task_execute():
    task = request.args.get('task')
    parameter = request.args.get('parameter')
    if not task or not parameter:
        return get_json_error('Missing task or parameter')
    if not re.fullmatch(r'\w+', task) or not re.fullmatch(r'[\w\-]+', parameter):
        return get_json_error('Invalid characters in task or parameter')
    try:
        _run_task_script(task, parameter)
    except ValueError as ve:
        return get_json_error(str(ve))
    except Exception:
        return get_json_error('Task execution failed', 500)
    return jsonify({'status': 'Task execution started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password is None:
        return get_json_error('Missing password')
    if password == app.config['ADMIN_PASSWORD']:
        return jsonify({'status': 'Access granted'})
    return make_response(jsonify({'status': 'Access denied'}), 401)

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    new_config = request.form.get('new_config')
    if password is None or new_config is None:
        return get_json_error('Missing password or new_config')
    if password == app.config['ADMIN_PASSWORD']:
        return jsonify({'status': 'Configuration updated', 'new_config': new_config})
    return make_response(jsonify({'status': 'Access denied'}), 401)

@app.route('/data/retrieve')
def data_retrieve():
    data_id = request.args.get('data_id')
    if not data_id:
        return get_json_error('Missing data_id')
    return jsonify({'data_id': data_id, 'data_value': 'Sample Value'})

@app.route('/data/delete', methods=['POST'])
def data_delete():
    data_id = request.form.get('data_id')
    if not data_id:
        return get_json_error('Missing data_id')
    return jsonify({'status': 'Data deleted', 'data_id': data_id})

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password is None or new_password is None:
        return get_json_error('Missing old_password or new_password')
    if old_password == app.config['ADMIN_PASSWORD']:
        app.config['ADMIN_PASSWORD'] = new_password
        os.environ['ADMIN_PASSWORD'] = new_password
        return jsonify({'status': 'Password changed successfully'})
    return make_response(jsonify({'status': 'Access denied', 'message': 'Invalid old password'}), 401)

@app.route('/task/status')
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return get_json_error('Missing task_id')
    return jsonify({'status': 'Running', 'task_id': task_id})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if password is None or new_setting is None:
        return get_json_error('Missing password or new_setting')
    if password == app.config['ADMIN_PASSWORD']:
        return jsonify({'status': 'Setting applied', 'new_setting': new_setting})
    return make_response(jsonify({'status': 'Access denied'}), 401)

@app.route('/task/logs')
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return get_json_error('Missing task_id')
    return jsonify({'status': 'Task logs', 'task_id': task_id, 'logs': f'Sample logs for task {task_id}'})

@app.route('/data/export')
def data_export():
    fmt = request.args.get('format', 'csv')
    if fmt not in {'csv', 'json', 'xml'}:
        return get_json_error('Unsupported export format')
    try:
        _export_data(fmt)
    except Exception:
        return get_json_error('Export failed', 500)
    return jsonify({'status': 'Data export started'})

@app.route('/user/profile')
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return get_json_error('Missing user_id')
    return jsonify({'user_id': user_id, 'name': 'John Doe', 'email': 'john.doe@example.com'})

if __name__ == '__main__':
    app.run(debug=False)