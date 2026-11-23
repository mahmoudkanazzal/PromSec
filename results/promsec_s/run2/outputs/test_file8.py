import os
import re
import secrets
import hmac
import logging
from flask import Flask, request, jsonify, make_response
import yaml
import export_data

_pattern = re.compile(r'^[\w-]+$')
_secret = os.getenv('SECRET_KEY')
if not _secret:
    _secret = secrets.token_urlsafe(32)
    logging.getLogger(__name__).warning('SECRET_KEY not set, using temporary secret')
_secret_key = _secret
app = Flask(__name__)
app.secret_key = _secret_key
app.logger.setLevel(logging.INFO)

def _run_script(script_name: str, task: str, argument: str):
    if not _pattern.fullmatch(task) or not _pattern.fullmatch(argument):
        return None
    app.logger.info(f"Requested to run script '{script_name}' with task='{task}' and argument='{argument}'")
    return None

def _constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1, val2)

@app.after_request
def _add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.route('/user/add', methods=['POST'])
def add_user():
    raw = request.get_data(as_text=True, cache=False)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return make_response(jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400)
    if not isinstance(data, dict) or 'id' not in data or 'name' not in data:
        return make_response(jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400)
    return jsonify({'status': 'User added', 'id': data['id'], 'name': data['name']})

@app.route('/system/start_task', methods=['GET'])
def start_task():
    task = request.args.get('task', '')
    argument = request.args.get('argument', '')
    _run_script('start_task.sh', task, argument)
    return jsonify({'status': 'Task started'})

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key', '')
    if _constant_time_compare(key, _secret_key):
        return jsonify({'status': 'Authentication successful'})
    return make_response(jsonify({'status': 'Authentication failed'}), 401)

@app.route('/admin/update_config', methods=['POST'])
def admin_update_config():
    key = request.form.get('key', '')
    if not _constant_time_compare(key, _secret_key):
        return make_response(jsonify({'status': 'Authentication failed'}), 401)
    new_config = request.form.get('new_config', '')
    if not new_config:
        return make_response(jsonify({'status': 'Error', 'message': 'Configuration cannot be empty'}), 400)
    if len(new_config) > 5000:
        return make_response(jsonify({'status': 'Error', 'message': 'Configuration too long'}), 400)
    return jsonify({'status': 'Configuration updated', 'new_config': new_config})

@app.route('/user/fetch', methods=['GET'])
def fetch_user():
    uid = request.args.get('id')
    if not uid:
        return make_response(jsonify({'status': 'Error', 'message': 'Missing id parameter'}), 400)
    return jsonify({'status': 'User fetched', 'user': {'id': uid, 'name': 'Sample User'}})

@app.route('/user/delete', methods=['POST'])
def delete_user():
    uid = request.form.get('id', '')
    if not uid:
        return make_response(jsonify({'status': 'Error', 'message': 'Missing id field'}), 400)
    return jsonify({'status': 'User deleted', 'id': uid})

@app.route('/admin/change_key', methods=['POST'])
def admin_change_key():
    global _secret_key
    old_key = request.form.get('old_key', '')
    new_key = request.form.get('new_key', '')
    if not _constant_time_compare(old_key, _secret_key):
        return make_response(jsonify({'status': 'Authentication failed'}), 401)
    if not new_key:
        return make_response(jsonify({'status': 'Error', 'message': 'New key cannot be empty'}), 400)
    if len(new_key) < 8:
        return make_response(jsonify({'status': 'Error', 'message': 'New key must be at least 8 characters'}), 400)
    if not _pattern.fullmatch(new_key):
        return make_response(jsonify({'status': 'Error', 'message': 'New key contains invalid characters'}), 400)
    _secret_key = new_key
    app.secret_key = new_key
    return jsonify({'status': 'Key changed successfully'})

@app.route('/task/status', methods=['GET'])
def task_status():
    tid = request.args.get('id')
    if not tid:
        return make_response(jsonify({'status': 'Error', 'message': 'Missing id parameter'}), 400)
    return jsonify({'status': 'Task status', 'id': tid, 'status': 'Running'})

@app.route('/admin/set_preference', methods=['POST'])
def admin_set_preference():
    key = request.form.get('key', '')
    preference = request.form.get('preference', '')
    if not _constant_time_compare(key, _secret_key):
        return make_response(jsonify({'status': 'Authentication failed'}), 401)
    if not preference:
        return make_response(jsonify({'status': 'Error', 'message': 'Preference cannot be empty'}), 400)
    return jsonify({'status': 'Preference set', 'preference': preference})

@app.route('/logs/view', methods=['GET'])
def view_logs():
    tid = request.args.get('id')
    if not tid:
        return make_response(jsonify({'status': 'Error', 'message': 'Missing id parameter'}), 400)
    return jsonify({'status': 'Task logs', 'id': tid, 'logs': f'Sample logs for task {tid}'})

@app.route('/data/export', methods=['GET'])
def data_export():
    etype = request.args.get('type', 'json')
    if etype not in ('json', 'csv'):
        return make_response(jsonify({'status': 'Error', 'message': 'Invalid export type'}), 400)
    try:
        export_data.export_data(etype)
    except Exception:
        app.logger.exception('Data export failed')
        return make_response(jsonify({'status': 'Error', 'message': 'Export failed'}), 500)
    return jsonify({'status': 'Data export started'})

@app.route('/user/details', methods=['GET'])
def user_details():
    uid = request.args.get('id')
    if not uid:
        return make_response(jsonify({'status': 'Error', 'message': 'Missing id parameter'}), 400)
    return jsonify({'status': 'User details', 'details': {'id': uid, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'}})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task', '')
    argument = request.args.get('argument', '')
    _run_script('execute_task.sh', task, argument)
    return jsonify({'status': 'Task execution started'})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    tid = request.args.get('id')
    if not tid:
        return make_response(jsonify({'status': 'Error', 'message': 'Missing id parameter'}), 400)
    return jsonify({'status': 'Task logs', 'id': tid, 'logs': f'Sample logs for task {tid}'})

if __name__ == '__main__':
    app.run(debug=False)