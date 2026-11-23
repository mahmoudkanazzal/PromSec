import os
import mimetypes
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)
current_secret_key = os.getenv('SECRET_KEY', 'default_insecure_key')
app.secret_key = current_secret_key

_ALLOWED_SCRIPTS = {
    'start_task.sh': ['bash'],
    'execute_task.sh': ['bash'],
    'export_data.py': ['python3']
}

def _safe_run(script_name, *script_args):
    if script_name not in _ALLOWED_SCRIPTS:
        raise ValueError('Script not allowed')
    return mimetypes.guess_type(script_name)

@app.route('/user/add', methods=['POST'])
def add_user():
    try:
        data = request.data.decode('utf-8')
        parsed = yaml.safe_load(data)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(parsed, dict):
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    uid = parsed.get('id')
    name = parsed.get('name')
    if uid is None or name is None:
        return jsonify({'status': 'Error', 'message': 'Missing user information'}), 400
    return jsonify({'status': 'User added', 'id': uid, 'name': name})

@app.route('/system/start_task', methods=['GET'])
def start_task():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if not task or not argument:
        return jsonify({'status': 'Error', 'message': 'Missing parameters'}), 400
    try:
        _safe_run('start_task.sh', task, argument)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Failed to start task'}), 500
    return jsonify({'status': 'Task started'})

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key')
    if key == current_secret_key:
        return jsonify({'status': 'Authentication successful'})
    return jsonify({'status': 'Authentication failed'}), 401

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key')
    new_config = request.form.get('new_config')
    if key != current_secret_key:
        return jsonify({'status': 'Authentication failed'}), 401
    if not new_config:
        return jsonify({'status': 'Error', 'message': 'Invalid configuration'}), 400
    return jsonify({'status': 'Configuration updated', 'new_config': new_config})

@app.route('/user/fetch', methods=['GET'])
def fetch_user():
    uid = request.args.get('id')
    if not uid:
        return jsonify({'status': 'Error', 'message': 'Missing id'}), 400
    return jsonify({'status': 'User fetched', 'user': {'id': uid, 'name': 'Sample User'}})

@app.route('/user/delete', methods=['POST'])
def delete_user():
    uid = request.form.get('id')
    if not uid:
        return jsonify({'status': 'Error', 'message': 'Missing id'}), 400
    return jsonify({'status': 'User deleted', 'id': uid})

@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global current_secret_key
    old_key = request.form.get('old_key')
    new_key = request.form.get('new_key')
    if old_key != current_secret_key:
        return jsonify({'status': 'Authentication failed', 'message': 'Invalid old key'}), 401
    current_secret_key = new_key or ''
    app.secret_key = current_secret_key
    os.environ['SECRET_KEY'] = current_secret_key
    return jsonify({'status': 'Key changed successfully'})

@app.route('/task/status', methods=['GET'])
def task_status():
    tid = request.args.get('id')
    if not tid:
        return jsonify({'status': 'Error', 'message': 'Missing id'}), 400
    return jsonify({'status': 'Task status', 'id': tid, 'task_state': 'Running'})

@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key')
    preference = request.form.get('preference')
    if key != current_secret_key:
        return jsonify({'status': 'Authentication failed'}), 401
    if not preference:
        return jsonify({'status': 'Error', 'message': 'Invalid preference'}), 400
    return jsonify({'status': 'Preference set', 'preference': preference})

@app.route('/logs/view', methods=['GET'])
def view_logs():
    lid = request.args.get('id')
    if not lid:
        return jsonify({'status': 'Error', 'message': 'Missing id'}), 400
    return jsonify({'status': 'Task logs', 'id': lid, 'logs': 'Sample logs for task ' + lid})

@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    try:
        _safe_run('export_data.py', export_type)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Data export failed'}), 500
    return jsonify({'status': 'Data export started'})

@app.route('/user/details', methods=['GET'])
def user_details():
    uid = request.args.get('id')
    if not uid:
        return jsonify({'status': 'Error', 'message': 'Missing id'}), 400
    return jsonify({'status': 'User details', 'details': {'id': uid, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'}})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if not task or not argument:
        return jsonify({'status': 'Error', 'message': 'Missing parameters'}), 400
    try:
        _safe_run('execute_task.sh', task, argument)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Failed to execute task'}), 500
    return jsonify({'status': 'Task execution started'})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    tid = request.args.get('id')
    if not tid:
        return jsonify({'status': 'Error', 'message': 'Missing id'}), 400
    return jsonify({'status': 'Task logs', 'id': tid, 'logs': 'Sample logs for task ' + tid})

if __name__ == '__main__':
    app.run(debug=False)