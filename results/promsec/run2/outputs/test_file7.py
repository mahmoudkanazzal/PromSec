import os
import subprocess
from flask import Flask, request, jsonify
import yaml
import re

app = Flask(__name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'default_insecure_key')
ALLOWED_PROCESSES = {'process1', 'process2'}
ALLOWED_EXPORT_TYPES = {'json', 'csv'}

def is_safe_name(value: str) -> bool:
    return bool(value) and re.fullmatch(r'[\w-]+', value) is not None

@app.route('/system/add_record', methods=['POST'])
def add_record():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    record_id = data.get('id')
    value = data.get('value')
    if record_id is None or value is None:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    return jsonify({'status': 'Record added', 'id': record_id, 'value': value}), 200

@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process', '')
    argument = request.args.get('argument', '')
    if not is_safe_name(process) or not is_safe_name(argument):
        return jsonify({'status': 'Error', 'message': 'Invalid process or argument'}), 400
    if process not in ALLOWED_PROCESSES:
        return jsonify({'status': 'Error', 'message': 'Process not allowed'}), 403
    try:
        subprocess.run(['bash', 'start_process.sh', process, argument], check=True, capture_output=True, text=True, timeout=30)
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'Error', 'message': f'Process failed: {e.stderr}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'Error', 'message': 'Process timed out'}), 504
    return jsonify({'status': 'Process started'}), 200

@app.route('/admin/authenticate', methods=['POST'])
def authenticate():
    key = request.form.get('key')
    if key == SECRET_KEY:
        return jsonify({'status': 'Authentication successful'}), 200
    return jsonify({'status': 'Authentication failed'}), 401

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key')
    new_config = request.form.get('new_config')
    if key != SECRET_KEY:
        return jsonify({'status': 'Authentication failed'}), 401
    if not new_config:
        return jsonify({'status': 'Error', 'message': 'Invalid configuration'}), 400
    return jsonify({'status': 'Configuration updated', 'new_config': new_config}), 200

@app.route('/records/fetch', methods=['GET'])
def fetch_record():
    record_id = request.args.get('id')
    if not record_id:
        return jsonify({'status': 'Error', 'message': 'Record ID is required'}), 400
    return jsonify({'status': 'Record fetched', 'record': {'id': record_id, 'value': 'Sample Value'}}), 200

@app.route('/records/delete', methods=['POST'])
def delete_record():
    record_id = request.form.get('id')
    if not record_id:
        return jsonify({'status': 'Error', 'message': 'Record ID is required'}), 400
    return jsonify({'status': 'Record deleted', 'id': record_id}), 200

@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global SECRET_KEY
    old_key = request.form.get('old_key')
    new_key = request.form.get('new_key')
    if old_key == SECRET_KEY:
        SECRET_KEY = new_key
        return jsonify({'status': 'Key changed successfully'}), 200
    return jsonify({'status': 'Authentication failed', 'message': 'Invalid old key'}), 401

@app.route('/process/status', methods=['GET'])
def process_status():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify({'status': 'Error', 'message': 'Process ID is required'}), 400
    return jsonify({'status': 'Process status', 'id': proc_id, 'status': 'Running'}), 200

@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key')
    preference = request.form.get('preference')
    if key != SECRET_KEY:
        return jsonify({'status': 'Authentication failed'}), 401
    if not preference:
        return jsonify({'status': 'Error', 'message': 'Invalid preference'}), 400
    return jsonify({'status': 'Preference set', 'preference': preference}), 200

@app.route('/logs/view', methods=['GET'])
def view_logs():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify({'status': 'Error', 'message': 'Process ID is required'}), 400
    return jsonify({'status': 'Process logs', 'id': proc_id, 'logs': f'Sample logs for process {proc_id}'}), 200

@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    if export_type not in ALLOWED_EXPORT_TYPES:
        return jsonify({'status': 'Error', 'message': 'Unsupported export type'}), 400
    try:
        subprocess.run(['python3', 'export_data.py', export_type], check=True, capture_output=True, text=True, timeout=60)
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'Error', 'message': f'Export failed: {e.stderr}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'Error', 'message': 'Export timed out'}), 504
    return jsonify({'status': 'Data export started'}), 200

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'User ID is required'}), 400
    return jsonify({'status': 'User details', 'details': {'id': user_id, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'}}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)