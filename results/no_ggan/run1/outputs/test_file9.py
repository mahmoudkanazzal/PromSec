import os
import re
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import yaml

admin_pw = os.getenv('ADMIN_PASSWORD')
if not admin_pw:
    raise RuntimeError('Environment variable ADMIN_PASSWORD must be set')
ADMIN_PASSWORD_HASH = generate_password_hash(admin_pw)

SAFE_ARG_PATTERN = re.compile(r'^[\w\-]+$')
def _is_safe_argument(arg: str) -> bool:
    return bool(SAFE_ARG_PATTERN.fullmatch(arg))

app = Flask(__name__)

@app.route('/config/add', methods=['POST'])
def config_add():
    if request.is_json:
        data = request.get_json()
    else:
        try:
            data = yaml.safe_load(request.get_data(as_text=True))
        except yaml.YAMLError:
            return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    config_id = data.get('config_id')
    config_value = data.get('config_value')
    if not config_id or not config_value:
        return jsonify({'status': 'Error', 'message': 'Missing configuration information'}), 400
    return jsonify({'status': 'Configuration added', 'config_id': config_id, 'config_value': config_value})

@app.route('/job/execute', methods=['GET'])
def job_execute():
    job_name = request.args.get('job_name')
    parameter = request.args.get('parameter')
    if not job_name or not parameter or not _is_safe_argument(job_name) or not _is_safe_argument(parameter):
        return jsonify({'status': 'Error', 'message': 'Invalid job name or parameter'}), 400
    try:
        subprocess.run(['sh', 'execute_job.sh', job_name, parameter], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Job execution failed'}), 500
    return jsonify({'status': 'Job execution started'})

@app.route('/auth/login', methods=['POST'])
def auth_login():
    password = request.form.get('password', '')
    if check_password_hash(ADMIN_PASSWORD_HASH, password):
        return jsonify({'status': 'Login successful'})
    return jsonify({'status': 'Login failed'}), 401

@app.route('/auth/update_password', methods=['POST'])
def auth_update_password():
    global ADMIN_PASSWORD_HASH
    password = request.form.get('password', '')
    if not check_password_hash(ADMIN_PASSWORD_HASH, password):
        return jsonify({'status': 'Login failed'}), 401
    new_password = request.form.get('new_password', '')
    if not new_password:
        return jsonify({'status': 'Error', 'message': 'Invalid new password'}), 400
    ADMIN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'status': 'Password updated'})

@app.route('/config/get', methods=['GET'])
def config_get():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({'status': 'Error', 'message': 'Configuration ID is required'}), 400
    config = {'config_id': config_id, 'config_value': 'Sample Value'}
    return jsonify({'status': 'Configuration retrieved', 'config': config})

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
    return jsonify({'status': 'Job status', 'job_id': job_id, 'status_detail': 'In Progress'})

@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password', '')
    if not check_password_hash(ADMIN_PASSWORD_HASH, password):
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
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ('json', 'csv', 'xml'):
        return jsonify({'status': 'Error', 'message': f"Unsupported format '{fmt}'"}), 400
    try:
        subprocess.run(['python', 'export_data.py', fmt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Data export failed'}), 500
    return jsonify({'status': 'Data export started'})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'User ID is required'}), 400
    user = {'user_id': user_id, 'name': 'John Doe', 'email': 'john.doe@example.com'}
    return jsonify({'status': 'User information retrieved', 'user_info': user})

if __name__ == '__main__':
    app.run(debug=False)