import os, re, hmac, subprocess
from flask import Flask, request, jsonify
import yaml

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('Environment variable SECRET_KEY must be set')
SAFE_ARG_PATTERN = re.compile(r'^[\w-]+$')
def is_safe_argument(value: str) -> bool:
    return bool(SAFE_ARG_PATTERN.fullmatch(value))
def constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1, val2)
app = Flask(__name__)
app.secret_key = SECRET_KEY
@app.route('/user/add', methods=['POST'])
def user_add():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify(status='Error', message='Invalid YAML format'), 400
    if not isinstance(data, dict):
        return jsonify(status='Error', message='YAML must represent a mapping'), 400
    user_id = data.get('id')
    name = data.get('name')
    if not user_id or not name:
        return jsonify(status='Error', message='Missing user information'), 400
    return jsonify(status='User added', id=user_id, name=name)
@app.route('/system/start_task', methods=['GET'])
def system_start_task():
    task = request.args.get('task', '')
    argument = request.args.get('argument', '')
    if not is_safe_argument(task) or not is_safe_argument(argument):
        return jsonify(status='Error', message='Invalid task or argument'), 400
    try:
        subprocess.run(['bash', 'start_task.sh', task, argument], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify(status='Error', message='Failed to start task'), 500
    return jsonify(status='Task started')
@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key', '')
    if constant_time_compare(key, SECRET_KEY):
        return jsonify(status='Authentication successful')
    return jsonify(status='Authentication failed'), 401
@app.route('/admin/update_config', methods=['POST'])
def admin_update_config():
    key = request.form.get('key', '')
    new_config = request.form.get('new_config', '')
    if not constant_time_compare(key, SECRET_KEY):
        return jsonify(status='Authentication failed'), 401
    if not new_config:
        return jsonify(status='Error', message='Invalid configuration'), 400
    return jsonify(status='Configuration updated', new_config=new_config)
@app.route('/user/fetch', methods=['GET'])
def user_fetch():
    user_id = request.args.get('id', '')
    if not user_id:
        return jsonify(status='Error', message='User ID is required'), 400
    return jsonify(status='User fetched', user={'id': user_id, 'name': 'Sample User'})
@app.route('/user/delete', methods=['POST'])
def user_delete():
    user_id = request.form.get('id', '')
    if not user_id:
        return jsonify(status='Error', message='User ID is required'), 400
    return jsonify(status='User deleted', id=user_id)
@app.route('/admin/change_key', methods=['POST'])
def admin_change_key():
    global SECRET_KEY
    old_key = request.form.get('old_key', '')
    new_key = request.form.get('new_key', '')
    if not constant_time_compare(old_key, SECRET_KEY):
        return jsonify(status='Authentication failed', message='Invalid old key'), 401
    if not new_key:
        return jsonify(status='Error', message='New key must not be empty'), 400
    SECRET_KEY = new_key
    app.secret_key = new_key
    return jsonify(status='Key changed successfully')
@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('id', '')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    return jsonify(status='Task status', id=task_id, state='Running')
@app.route('/admin/set_preference', methods=['POST'])
def admin_set_preference():
    key = request.form.get('key', '')
    if not constant_time_compare(key, SECRET_KEY):
        return jsonify(status='Authentication failed'), 401
    preference = request.form.get('preference', '')
    if not preference:
        return jsonify(status='Error', message='Invalid preference'), 400
    return jsonify(status='Preference set', preference=preference)
@app.route('/logs/view', methods=['GET'])
def logs_view():
    task_id = request.args.get('id', '')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    return jsonify(status='Task logs', id=task_id, logs=f'Sample logs for task {task_id}')
@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    if not is_safe_argument(export_type):
        return jsonify(status='Error', message='Invalid export type'), 400
    try:
        subprocess.run(['python3', 'export_data.py', export_type], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify(status='Error', message='Data export failed'), 500
    return jsonify(status='Data export started')
@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id', '')
    if not user_id:
        return jsonify(status='Error', message='User ID is required'), 400
    return jsonify(status='User details', details={'id': user_id, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'})
@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task', '')
    argument = request.args.get('argument', '')
    if not is_safe_argument(task) or not is_safe_argument(argument):
        return jsonify(status='Error', message='Invalid task or argument'), 400
    try:
        subprocess.run(['bash', 'execute_task.sh', task, argument], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify(status='Error', message='Task execution failed'), 500
    return jsonify(status='Task execution started')
@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('id', '')
    if not task_id:
        return jsonify(status='Error', message='Task ID is required'), 400
    return jsonify(status='Task logs', id=task_id, logs=f'Sample logs for task {task_id}')
if __name__ == '__main__':
    app.run(debug=False)