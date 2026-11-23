import os
import re
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'top_secret_2024')
app.secret_key = SECRET_KEY

def _auth(key):
    return key == SECRET_KEY

def _is_safe_name(name):
    return bool(name) and re.fullmatch(r'[\w\-.]+', name) is not None

def _start_process_safe(process, argument):
    if not _is_safe_name(process) or not _is_safe_name(argument):
        return False, 'Invalid characters in process name or argument.'
    return True, 'Process started safely.'

def _export_data_safe(export_type):
    allowed = {'json', 'csv', 'xml'}
    if export_type not in allowed:
        return False, f'Unsupported export type: {export_type}'
    return True, 'Data export initiated safely.'

@app.route('/system/add_record', methods=['POST'])
def add_record():
    try:
        raw = request.data.decode('utf-8')
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify(status='Error', message='Invalid YAML format'), 400
    if not isinstance(data, dict):
        return jsonify(status='Error', message='Invalid YAML format'), 400
    rec_id = data.get('id')
    value = data.get('value')
    if rec_id is None or value is None:
        return jsonify(status='Error', message='Missing record information'), 400
    return jsonify(status='Record added', id=rec_id, value=value)

@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process', '')
    argument = request.args.get('argument', '')
    success, message = _start_process_safe(process, argument)
    if not success:
        return jsonify(status='Error', message=message), 400
    return jsonify(status='Process started', detail=message)

@app.route('/admin/authenticate', methods=['POST'])
def authenticate():
    key = request.form.get('key', '')
    if _auth(key):
        return jsonify(status='Authentication successful')
    return jsonify(status='Authentication failed'), 401

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key', '')
    if not _auth(key):
        return jsonify(status='Authentication failed'), 401
    new_config = request.form.get('new_config')
    if new_config is None:
        return jsonify(status='Error', message='Invalid configuration'), 400
    return jsonify(status='Configuration updated', new_config=new_config)

@app.route('/records/fetch', methods=['GET'])
def fetch_record():
    rec_id = request.args.get('id')
    if not rec_id:
        return jsonify(status='Error', message='Record ID is required'), 400
    return jsonify(status='Record fetched', record={'id': rec_id, 'value': 'Sample Value'})

@app.route('/records/delete', methods=['POST'])
def delete_record():
    rec_id = request.form.get('id')
    if not rec_id:
        return jsonify(status='Error', message='Record ID is required'), 400
    return jsonify(status='Record deleted', id=rec_id)

@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global SECRET_KEY
    old_key = request.form.get('old_key', '')
    new_key = request.form.get('new_key')
    if old_key == SECRET_KEY:
        SECRET_KEY = new_key if new_key else ''
        app.secret_key = SECRET_KEY
        return jsonify(status='Key changed successfully')
    return jsonify(status='Authentication failed', message='Invalid old key'), 401

@app.route('/process/status', methods=['GET'])
def process_status():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify(status='Error', message='Process ID is required'), 400
    return jsonify(status='Process status', id=proc_id, process_state='Running')

@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key', '')
    if not _auth(key):
        return jsonify(status='Authentication failed'), 401
    preference = request.form.get('preference')
    if preference is None:
        return jsonify(status='Error', message='Invalid preference'), 400
    return jsonify(status='Preference set', preference=preference)

@app.route('/logs/view', methods=['GET'])
def view_logs():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify(status='Error', message='Process ID is required'), 400
    return jsonify(status='Process logs', id=proc_id, logs='Sample logs for process ' + proc_id)

@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    success, message = _export_data_safe(export_type)
    if not success:
        return jsonify(status='Error', message=message), 400
    return jsonify(status='Data export started', detail=message)

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify(status='Error', message='User ID is required'), 400
    return jsonify(status='User details', details={'id': user_id, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'})

if __name__ == '__main__':
    app.run(debug=False)