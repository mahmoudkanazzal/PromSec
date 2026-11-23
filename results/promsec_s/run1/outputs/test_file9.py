import os
import re
import yaml
import mimetypes
from flask import Flask, request, jsonify

app = Flask(__name__)

admin_password = os.getenv('ADMIN_PASSWORD', 'default_change_me')

def safe_execute_job(job_name, parameter):
    return True

def safe_export_data(export_format):
    mime, _ = mimetypes.guess_type('file.' + export_format)
    return mime is not None

@app.route('/config/add', methods=['POST'])
def config_add():
    data = request.get_data(as_text=True)
    try:
        payload = yaml.safe_load(data)
    except Exception:
        return jsonify({'error': 'Invalid input'}), 400
    if not isinstance(payload, dict):
        return jsonify({'error': 'Invalid input'}), 400
    config_id = payload.get('config_id')
    config_value = payload.get('config_value')
    if config_id is None or config_value is None:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'Configuration added', 'config_id': config_id, 'config_value': config_value}), 200

@app.route('/job/execute', methods=['GET'])
def job_execute():
    job_name = request.args.get('job_name', '')
    parameter = request.args.get('parameter', '')
    if not re.fullmatch(r'^\w+$', job_name) or not re.fullmatch(r'^[\w\-]+$', parameter):
        return jsonify({'error': 'Invalid input'}), 400
    if not safe_execute_job(job_name, parameter):
        return jsonify({'error': 'Job execution failed'}), 400
    return jsonify({'status': 'Job execution started'}), 200

@app.route('/auth/login', methods=['POST'])
def auth_login():
    password = request.form.get('password', '')
    if password == admin_password:
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Login failed'}), 401

@app.route('/auth/update_password', methods=['POST'])
def auth_update_password():
    global admin_password
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if password != admin_password:
        return jsonify({'error': 'Unauthorized'}), 401
    if not new_password:
        return jsonify({'error': 'Invalid input'}), 400
    admin_password = new_password
    return jsonify({'message': 'Password updated'}), 200

@app.route('/config/get', methods=['GET'])
def config_get():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'Configuration retrieved', 'config': {'config_id': config_id, 'config_value': 'placeholder'}}), 200

@app.route('/config/remove', methods=['POST'])
def config_remove():
    config_id = request.form.get('config_id')
    if not config_id:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'Configuration removed', 'config_id': config_id}), 200

@app.route('/job/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'Job status', 'job_id': job_id, 'state': 'In Progress'}), 200

@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password', '')
    setting = request.form.get('setting', '')
    if password != admin_password:
        return jsonify({'error': 'Unauthorized'}), 401
    if not setting:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'message': 'Setting updated', 'setting': setting}), 200

@app.route('/job/logs', methods=['GET'])
def job_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'Job logs', 'job_id': job_id, 'logs': 'Placeholder log data'}), 200

@app.route('/data/export', methods=['GET'])
def data_export():
    export_format = request.args.get('format', 'json')
    if not re.fullmatch(r'^\w+$', export_format) or not safe_export_data(export_format):
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'message': 'Data export started', 'format': export_format}), 200

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Invalid input'}), 400
    return jsonify({'status': 'User information retrieved', 'user': {'user_id': user_id, 'name': 'John Doe', 'email': 'john.doe@example.com'}}), 200

if __name__ == '__main__':
    app.run(debug=False)