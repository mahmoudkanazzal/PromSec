from flask import Flask, request, jsonify
import os
from yaml import safe_load
import mimetypes

app = Flask(__name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')


@app.route('/system/add_record', methods=['POST'])
def add_record():
    try:
        raw = request.get_data(as_text=True)
        data = safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid record format'}), 400
    rec_id = data.get('id')
    value = data.get('value')
    if rec_id is None or value is None:
        return jsonify({'error': 'Missing id or value'}), 400
    return jsonify({'id': rec_id, 'value': value})


@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process')
    argument = request.args.get('argument')
    if not process or not argument:
        return jsonify({'error': 'Missing process or argument'}), 400
    mimetypes.guess_type(process)
    return jsonify({'status': 'started', 'process': process, 'argument': argument})


@app.route('/admin/authenticate', methods=['POST'])
def authenticate():
    key = request.form.get('key')
    if key == SECRET_KEY:
        return jsonify({'status': 'authenticated'})
    return jsonify({'error': 'Unauthorized'}), 401


@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key')
    new_config = request.form.get('new_config')
    if key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    if new_config is None:
        return jsonify({'error': 'Missing new_config'}), 400
    return jsonify({'status': 'config updated', 'new_config': new_config})


@app.route('/records/fetch', methods=['GET'])
def fetch_record():
    rec_id = request.args.get('id')
    if not rec_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'id': rec_id, 'value': 'sample value'})


@app.route('/records/delete', methods=['POST'])
def delete_record():
    rec_id = request.form.get('id')
    if not rec_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'status': f'record {rec_id} deleted'})


@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global SECRET_KEY
    old_key = request.form.get('old_key')
    new_key = request.form.get('new_key')
    if old_key == SECRET_KEY:
        SECRET_KEY = new_key
        return jsonify({'status': 'key changed'})
    return jsonify({'error': 'Unauthorized'}), 401


@app.route('/process/status', methods=['GET'])
def process_status():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'id': proc_id, 'status': 'running'})


@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key')
    preference = request.form.get('preference')
    if key != SECRET_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    if preference is None:
        return jsonify({'error': 'Missing preference'}), 400
    return jsonify({'status': 'preference set', 'preference': preference})


@app.route('/logs/view', methods=['GET'])
def view_logs():
    log_id = request.args.get('id')
    if not log_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'log': f'Log entry for {log_id}'})


@app.route('/data/export', methods=['GET'])
def export_data():
    export_type = request.args.get('type', 'json')
    mimetypes.guess_type(f'file.{export_type}')
    return jsonify({'status': 'export started', 'type': export_type})


@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'Missing id'}), 400
    return jsonify({'id': user_id, 'name': 'Alice Smith', 'email': 'alice.smith@example.com'})


if __name__ == '__main__':
    app.run(debug=False)