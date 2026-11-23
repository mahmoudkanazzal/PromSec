import os
import re
import secrets
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import yaml

app = Flask(__name__)

admin_password = os.getenv('ADMIN_PASSWORD')
if not admin_password:
    admin_password = secrets.token_urlsafe(16)
    print('Warning: ADMIN_PASSWORD not set, using temporary password')
password_hash = generate_password_hash(admin_password)

def is_safe_job_name(name: str) -> bool:
    return re.fullmatch(r'[A-Za-z0-9_-]+', name) is not None

def is_safe_parameter(param: str) -> bool:
    return re.fullmatch(r'[A-Za-z0-9_.-]+', param) is not None

@app.route('/config/add', methods=['POST'])
def config_add():
    try:
        data = yaml.safe_load(request.data.decode('utf-8'))
    except yaml.YAMLError:
        return jsonify(message='Invalid YAML format'), 400
    if not isinstance(data, dict):
        return jsonify(message='YAML must define a mapping'), 400
    config_id = data.get('config_id')
    config_value = data.get('config_value')
    if config_id is None or config_value is None:
        return jsonify(message='Missing configuration information'), 400
    return jsonify(status='Configuration added', config_id=config_id, config_value=config_value)

@app.route('/job/execute', methods=['GET'])
def job_execute():
    job_name = request.args.get('job_name')
    parameter = request.args.get('parameter')
    if not job_name or not is_safe_job_name(job_name):
        return jsonify(message='Invalid job name'), 400
    if not parameter or not is_safe_parameter(parameter):
        return jsonify(message='Invalid parameter'), 400
    try:
        subprocess.run(['sh', 'execute_job.sh', job_name, parameter], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify(message='Job execution failed'), 500
    return jsonify(status='Job execution started')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    pwd = request.form.get('password', '')
    if check_password_hash(password_hash, pwd):
        return jsonify(status='Login successful')
    return jsonify(status='Login failed'), 401

@app.route('/auth/update_password', methods=['POST'])
def auth_update_password():
    global password_hash
    current = request.form.get('password', '')
    new = request.form.get('new_password', '')
    if not check_password_hash(password_hash, current):
        return jsonify(status='Login failed'), 401
    if not new:
        return jsonify(message='Invalid new password'), 400
    password_hash = generate_password_hash(new)
    return jsonify(status='Password updated')

@app.route('/config/get', methods=['GET'])
def config_get():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify(message='Configuration ID is required'), 400
    return jsonify(status='Configuration retrieved', config={'config_id': config_id, 'config_value': 'Sample Value'})

@app.route('/config/remove', methods=['POST'])
def config_remove():
    config_id = request.form.get('config_id')
    if not config_id:
        return jsonify(message='Configuration ID is required'), 400
    return jsonify(status='Configuration removed', config_id=config_id)

@app.route('/job/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify(message='Job ID is required'), 400
    return jsonify(status='Job status', job_id=job_id, job_state='In Progress')

@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    pwd = request.form.get('password', '')
    setting = request.form.get('setting', '')
    if not check_password_hash(password_hash, pwd):
        return jsonify(status='Access denied'), 401
    if not setting:
        return jsonify(message='Invalid setting'), 400
    return jsonify(status='Setting updated', setting=setting)

@app.route('/job/logs', methods=['GET'])
def job_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify(message='Job ID is required'), 400
    return jsonify(status='Job logs', job_id=job_id, logs=f'Logs for job {job_id}')

@app.route('/data/export', methods=['GET'])
def data_export():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ('json', 'csv', 'xml'):
        return jsonify(message=f"Unsupported format '{fmt}'"), 400
    try:
        subprocess.run(['python', 'export_data.py', fmt], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify(message='Data export failed'), 500
    return jsonify(status='Data export started')

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(message='User ID is required'), 400
    return jsonify(status='User information retrieved', user_info={'user_id': user_id, 'name': 'John Doe', 'email': 'john.doe@example.com'})

if __name__ == '__main__':
    app.run(debug=False)