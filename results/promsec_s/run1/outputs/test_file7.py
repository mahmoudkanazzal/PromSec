from flask import Flask, request, jsonify
import os
from yaml import safe_load
import mimetypes

app = Flask(__name__)

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = os.urandom(24).hex()


@app.route('/system/add_record', methods=['POST'])
def add_record():
    raw = request.get_data(as_text=True)
    try:
        data = safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError
        record_id = data['id']
        value = data['value']
    except Exception:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'Record added', 'id': record_id, 'value': value})


@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process')
    argument = request.args.get('argument')
    if not process:
        return jsonify({'error': 'Missing process parameter'}), 400
    mime, _ = mimetypes.guess_type(process)
    if mime is None:
        return jsonify({'error': 'Invalid process parameter'}), 400
    return jsonify({'status': 'Process started', 'process': process, 'argument': argument})


@app.route('/admin/authenticate', methods=['POST'])
def authenticate():
    key = request.form.get('key')
    if key == SECRET_KEY:
        return jsonify({'status': 'Authenticated'})
    return jsonify({'error': 'Unauthorized'}), 401


@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key')
    new_config = request.form.get('new_config')
    if key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    if not new_config:
        return jsonify({'error': 'Missing new_config'}), 400
    return jsonify({'status': 'Configuration updated', 'new_config': new_config})


@app.route('/records/fetch', methods=['GET'])
def fetch_record():
    record_id = request.args.get('id')
    if not record_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'id': record_id, 'value': 'Sample Value'})


@app.route('/records/delete', methods=['POST'])
def delete_record():
    record_id = request.form.get('id')
    if not record_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': 'Record deleted', 'id': record_id})


@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global SECRET_KEY
    old_key = request.form.get('old_key')
    new_key = request.form.get('new_key')
    if old_key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    if not new_key:
        return jsonify({'error': 'Missing new_key'}), 400
    SECRET_KEY = new_key
    return jsonify({'status': 'Key changed'})


@app.route('/process/status', methods=['GET'])
def process_status():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'id': proc_id, 'status': 'Running'})


@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key')
    preference = request.form.get('preference')
    if key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    if not preference:
        return jsonify({'error': 'Missing preference'}), 400
    return jsonify({'status': 'Preference set', 'preference': preference})


@app.route('/logs/view', methods=['GET'])
def view_logs():
    log_id = request.args.get('id')
    if not log_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'id': log_id, 'log': 'Dummy log entry'})


@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    dummy_filename = f'dummy.{export_type}'
    mime, _ = mimetypes.guess_type(dummy_filename)
    if mime is None:
        return jsonify({'error': 'Invalid export type'}), 400
    return jsonify({'status': 'Data export started', 'type': export_type})


@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'id': user_id, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'})


if __name__ == "__main__":
    app.run(debug=False)