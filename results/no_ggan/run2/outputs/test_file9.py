import os
import re
import subprocess
import yaml
import hmac
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv('ADMIN_PASSWORD', 'change_me_please'))

def verify_password(provided_password: str) -> bool:
    return check_password_hash(ADMIN_PASSWORD_HASH, provided_password or '')

def is_safe_job_param(value: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z0-9_-]+', value or ''))

@app.route('/config/add', methods=['POST'])
def config_add():
    try:
        data = yaml.safe_load(request.data.decode('utf-8'))
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'status': 'Error', 'message': 'YAML must define a mapping'}), 400
    config_id = data.get('config_id')
    config_value = data.get('config_value')
    if not config_id or not config_value:
        return jsonify({'status': 'Error', 'message': 'Missing configuration information'}), 400
    return jsonify({'status': 'Configuration added', 'config_id': config_id, 'config_value': config_value})

@app.route('/job/execute', methods=['GET'])
def job_execute():
    job_name = request.args.get('job_name')
    parameter = request.args.get('parameter')
    if not job_name or not is_safe_job_param(job_name):
        return jsonify({'status': 'Error', 'message': 'Invalid or missing job_name'}), 400
    if not parameter or not is_safe_job_param(parameter):
        return jsonify({'status': 'Error', 'message': 'Invalid or missing parameter'}), 400
    try:
        subprocess.run(['sh', 'execute_job.sh', job_name, parameter], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Failed to start job'}), 500
    return jsonify({'status': 'Job execution started'})

@app.route('/auth/login', methods=['POST'])
def auth_login():
    password = request.form.get('password', '')
    if verify_password(password):
        return jsonify({'status': 'Login successful'})
    return jsonify({'status': 'Login failed'}), 401

@app.route('/auth/update_password', methods=['POST'])
def auth_update_password():
    password = request.form.get('password', '')
    if not verify_password(password):
        return jsonify({'status': 'Login failed'}), 401
    new_password = request.form.get('new_password', '')
    if not new_password:
        return jsonify({'status': 'Error', 'message': 'Invalid new password'}), 400
    global ADMIN_PASSWORD_HASH
    ADMIN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'status': 'Password updated'})

@app.route('/config/get', methods=['GET'])
def config_get():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({'status': 'Error', 'message': 'Configuration ID is required'}), 400
    return jsonify({'status': 'Configuration retrieved', 'config': {'config_id': config_id, 'config_value': 'Sample Value'}})

@app.route('/config/remove', methods=['POST'])
def config_remove():
    config_id = request.form.get('config_id')
    if not config_id:
        return jsonify({'status': 'Error', 'message': 'Configuration ID is required'}), 400
    return jsonify({'status': 'Configuration removed', 'config_id': config_id})

@app.route('/job/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Job ID is required'}), 400
    return jsonify({'status': 'Job status', 'job_id': job_id, 'status': 'In Progress'})

@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password', '')
    if not verify_password(password):
        return jsonify({'status': 'Access denied'}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({'status': 'Error', 'message': 'Invalid setting'}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting})

@app.route('/job/logs', methods=['GET'])
def job_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Job ID is required'}), 400
    logs = f'Logs for job {job_id}'
    return jsonify({'status': 'Job logs', 'job_id': job_id, 'logs': logs})

@app.route('/data/export', methods=['GET'])
def data_export():
    export_format = request.args.get('format', 'json').lower()
    if export_format not in {'json', 'csv', 'xml'}:
        return jsonify({'status': 'Error', 'message': 'Unsupported format. Allowed: json, csv, xml'}), 400
    try:
        subprocess.run(['python', 'export_data.py', export_format], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Failed to start export'}), 500
    return jsonify({'status': 'Data export started'})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'User ID is required'}), 400
    return jsonify({'status': 'User information retrieved', 'user_info': {'user_id': user_id, 'name': 'John Doe', 'email': 'john.doe@example.com'}})

if __name__ == '__main__':
    app.run(debug=False)