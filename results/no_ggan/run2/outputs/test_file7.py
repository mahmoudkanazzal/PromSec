import os
import re
import hmac
import subprocess
import yaml
from flask import Flask, request, jsonify

_secret = os.getenv('SECRET_KEY')
if not _secret:
    raise RuntimeError('Environment variable SECRET_KEY must be set')
app = Flask(__name__)
app.config['SECRET_KEY'] = _secret.encode()
_alnum_pattern = re.compile(r'^[\w\-]+$')


def _check_secret(provided_key):
    if not isinstance(provided_key, str):
        return False
    return hmac.compare_digest(provided_key.encode(), app.config['SECRET_KEY'])


@app.route('/system/add_record', methods=['POST'])
def add_record():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'status': 'Error', 'message': 'YAML must define a mapping'}), 400
    rec_id = data.get('id')
    value = data.get('value')
    if not rec_id or not value:
        return jsonify({'status': 'Error', 'message': 'Missing record information'}), 400
    return jsonify({'status': 'Record added', 'id': rec_id, 'value': value})


@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process')
    argument = request.args.get('argument', '')
    if not process or not _alnum_pattern.match(process):
        return jsonify({'status': 'Error', 'message': 'Invalid process name'}), 400
    if argument and not _alnum_pattern.match(argument):
        return jsonify({'status': 'Error', 'message': 'Invalid argument'}), 400
    try:
        subprocess.run(['bash', 'start_process.sh', process, argument],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Failed to start process'}), 500
    return jsonify({'status': 'Process started'})


@app.route('/admin/authenticate', methods=['POST'])
def authenticate():
    key = request.form.get('key')
    if _check_secret(key):
        return jsonify({'status': 'Authentication successful'})
    return jsonify({'status': 'Authentication failed'}), 401


@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key')
    new_config = request.form.get('new_config')
    if not _check_secret(key):
        return jsonify({'status': 'Authentication failed'}), 401
    if not new_config:
        return jsonify({'status': 'Error', 'message': 'Invalid configuration'}), 400
    return jsonify({'status': 'Configuration updated', 'new_config': new_config})


@app.route('/records/fetch', methods=['GET'])
def fetch_record():
    record_id = request.args.get('id')
    if not record_id:
        return jsonify({'status': 'Error', 'message': 'Record ID is required'}), 400
    return jsonify({'status': 'Record fetched', 'record': {'id': record_id, 'value': 'Sample Value'}})


@app.route('/records/delete', methods=['POST'])
def delete_record():
    record_id = request.form.get('id')
    if not record_id:
        return jsonify({'status': 'Error', 'message': 'Record ID is required'}), 400
    return jsonify({'status': 'Record deleted', 'id': record_id})


@app.route('/admin/change_key', methods=['POST'])
def change_key():
    old_key = request.form.get('old_key')
    new_key = request.form.get('new_key')
    if not new_key:
        return jsonify({'status': 'Error', 'message': 'New key must not be empty'}), 400
    if _check_secret(old_key):
        app.config['SECRET_KEY'] = new_key.encode()
        return jsonify({'status': 'Key changed successfully'})
    return jsonify({'status': 'Authentication failed', 'message': 'Invalid old key'}), 401


@app.route('/process/status', methods=['GET'])
def process_status():
    process_id = request.args.get('id')
    if not process_id:
        return jsonify({'status': 'Error', 'message': 'Process ID is required'}), 400
    return jsonify({'status': 'Process status', 'id': process_id, 'status': 'Running'})


@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key')
    if not _check_secret(key):
        return jsonify({'status': 'Authentication failed'}), 401
    preference = request.form.get('preference')
    if not preference:
        return jsonify({'status': 'Error', 'message': 'Invalid preference'}), 400
    return jsonify({'status': 'Preference set', 'preference': preference})


@app.route('/logs/view', methods=['GET'])
def view_logs():
    process_id = request.args.get('id')
    if not process_id:
        return jsonify({'status': 'Error', 'message': 'Process ID is required'}), 400
    return jsonify({'status': 'Process logs', 'id': process_id, 'logs': f'Sample logs for process {process_id}'})


@app.route('/data/export', methods=['GET'])
def export_data():
    export_type = request.args.get('type', 'json')
    allowed = {'json', 'csv', 'xml'}
    if export_type not in allowed:
        return jsonify({'status': 'Error', 'message': 'Invalid export type'}), 400
    try:
        subprocess.run(['python3', 'export_data.py', export_type],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Data export failed'}), 500
    return jsonify({'status': 'Data export started'})


@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'User ID is required'}), 400
    return jsonify({'status': 'User details', 'details': {'id': user_id, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'}})


if __name__ == '__main__':
    app.run(debug=False)