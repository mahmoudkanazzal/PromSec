import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def validate_yaml(data):
    try:
        return yaml.safe_load(data)
    except Exception:
        return None

def is_safe_token(token):
    return bool(re.fullmatch(r'^[\w-]+$', token))

admin_hash_env = os.getenv('ADMIN_PASSWORD')
if admin_hash_env:
    password_hash = admin_hash_env
else:
    password_hash = generate_password_hash('admin_pass_2024')

@app.route('/config/upload', methods=['POST'])
def config_upload():
    raw = request.get_data(as_text=True)
    parsed = validate_yaml(raw)
    if not isinstance(parsed, dict):
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    name = parsed.get('config_name')
    value = parsed.get('config_value')
    if not name or not value:
        return jsonify({'status': 'Error', 'message': 'Missing required fields'}), 400
    return jsonify({'status': 'Configuration uploaded', 'config_name': name, 'config_value': value})

@app.route('/service/execute', methods=['GET'])
def service_execute():
    service = request.args.get('service')
    param = request.args.get('param')
    if not service or not is_safe_token(service):
        return jsonify({'status': 'Error', 'message': 'Invalid service token'}), 400
    if param and not is_safe_token(param):
        return jsonify({'status': 'Error', 'message': 'Invalid param token'}), 400
    cmd = ['bash', 'run_service.sh', service]
    if param:
        cmd.append(param)
    try:
        subprocess.run(cmd, check=False)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Failed to start service'}), 500
    return jsonify({'status': 'Service execution started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    pwd = request.form.get('password', '')
    if check_password_hash(password_hash, pwd):
        return jsonify('Login successful')
    return jsonify('Login failed'), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global password_hash
    current = request.form.get('current_password', '')
    new = request.form.get('new_password', '')
    if not check_password_hash(password_hash, current):
        return jsonify('Unauthorized'), 401
    if not new:
        return jsonify({'status': 'Error', 'message': 'New password cannot be empty'}), 400
    password_hash = generate_password_hash(new)
    return jsonify('Password updated')

@app.route('/config/retrieve', methods=['GET'])
def config_retrieve():
    name = request.args.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'config_name is required'}), 400
    return jsonify({'status': 'Configuration retrieved', 'config': {'config_name': name, 'config_value': 'Sample Config Value'}})

@app.route('/config/delete', methods=['POST'])
def config_delete():
    name = request.form.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'config_name is required'}), 400
    return jsonify({'status': 'Configuration deleted', 'config_name': name})

@app.route('/service/status', methods=['GET'])
def service_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'job_id is required'}), 400
    return jsonify({'status': 'Service status', 'job_id': job_id, 'service_status': 'Running'})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    pwd = request.form.get('password', '')
    setting = request.form.get('setting')
    if not check_password_hash(password_hash, pwd):
        return jsonify('Unauthorized'), 401
    if not setting:
        return jsonify({'status': 'Error', 'message': 'setting is required'}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting})

@app.route('/service/logs', methods=['GET'])
def service_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'job_id is required'}), 400
    return jsonify({'status': 'Service logs', 'job_id': job_id, 'logs': f'Sample logs for job {job_id}'})

@app.route('/backup/data', methods=['GET'])
def backup_data():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ('json', 'yaml', 'csv'):
        return jsonify({'status': 'Error', 'message': 'Invalid format'}), 400
    cmd = ['python3', 'backup_data.py', fmt]
    try:
        subprocess.run(cmd, check=False)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Backup failed'}), 500
    return jsonify({'status': 'Data backup started'})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'user_id is required'}), 400
    return jsonify({'status': 'User information retrieved', 'user': {'user_id': user_id, 'name': 'John Doe', 'email': 'john@example.com'}})

if __name__ == '__main__':
    app.run(debug=False)