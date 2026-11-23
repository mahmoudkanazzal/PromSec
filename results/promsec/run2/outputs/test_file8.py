import os
import yaml
import subprocess
from flask import Flask, request, jsonify

secret_key = os.getenv('SECRET_KEY', 'top_secret_2024')
app = Flask(__name__)
app.secret_key = secret_key

@app.route('/user/add', methods=['POST'])
def add_user():
    data = request.get_data(as_text=True)
    try:
        payload = yaml.safe_load(data)
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(payload, dict) or 'id' not in payload or 'name' not in payload:
        return jsonify({'error': 'Missing required fields'}), 400
    return jsonify({'status': 'User added', 'id': payload['id'], 'name': payload['name']})

@app.route('/system/start_task', methods=['GET'])
def start_task():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if not task or not argument:
        return jsonify({'error': 'Missing parameters'}), 400
    subprocess.run(['bash', 'start_task.sh', task, argument], capture_output=True, text=True)
    return jsonify({'status': 'Task started'})

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key')
    if key == secret_key:
        return jsonify({'status': 'Authentication successful'})
    return jsonify({'status': 'Authentication failed'}), 401

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key')
    if key != secret_key:
        return jsonify({'status': 'Authentication failed'}), 401
    new_config = request.form.get('new_config')
    if not new_config:
        return jsonify({'error': 'Missing new_config'}), 400
    return jsonify({'status': 'Configuration updated', 'new_config': new_config})

@app.route('/user/fetch', methods=['GET'])
def fetch_user():
    uid = request.args.get('id')
    if not uid:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'User fetched', 'user': {'id': uid, 'name': 'Sample User'}})

@app.route('/user/delete', methods=['POST'])
def delete_user():
    uid = request.form.get('id')
    if not uid:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'User deleted', 'id': uid})

@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global secret_key
    old_key = request.form.get('old_key')
    new_key = request.form.get('new_key')
    if not old_key or not new_key:
        return jsonify({'error': 'Missing keys'}), 400
    if old_key == secret_key:
        secret_key = new_key
        app.secret_key = new_key
        return jsonify({'status': 'Key changed successfully'})
    return jsonify({'status': 'Authentication failed', 'message': 'Invalid old key'}), 401

@app.route('/task/status', methods=['GET'])
def task_status():
    tid = request.args.get('id')
    if not tid:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'Task status', 'id': tid, 'status': 'Running'})

@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key')
    if key != secret_key:
        return jsonify({'status': 'Authentication failed'}), 401
    pref = request.form.get('preference')
    if not pref:
        return jsonify({'error': 'Missing preference'}), 400
    return jsonify({'status': 'Preference set', 'preference': pref})

@app.route('/logs/view', methods=['GET'])
def view_logs():
    tid = request.args.get('id')
    if not tid:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'Task logs', 'id': tid, 'logs': 'Sample logs for task ' + tid})

@app.route('/data/export', methods=['GET'])
def data_export():
    dtype = request.args.get('type', 'json')
    subprocess.run(['python3', 'export_data.py', dtype], capture_output=True, text=True)
    return jsonify({'status': 'Data export started'})

@app.route('/user/details', methods=['GET'])
def user_details():
    uid = request.args.get('id')
    if not uid:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'User details', 'details': {'id': uid, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'}})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if not task or not argument:
        return jsonify({'error': 'Missing parameters'}), 400
    subprocess.run(['bash', 'execute_task.sh', task, argument], capture_output=True, text=True)
    return jsonify({'status': 'Task execution started'})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    tid = request.args.get('id')
    if not tid:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'Task logs', 'id': tid, 'logs': 'Sample logs for task ' + tid})

if __name__ == '__main__':
    app.run(debug=False)