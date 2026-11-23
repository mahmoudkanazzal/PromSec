import os
import hmac
import re
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = os.urandom(32).hex()
app.secret_key = SECRET_KEY

ALLOWED_COMMANDS = {'status', 'restart', 'stop'}

class ConfigManager:
    @staticmethod
    def load_config(yaml_data):
        try:
            return yaml.safe_load(yaml_data)
        except yaml.YAMLError:
            return None
    @staticmethod
    def validate_config(config):
        return isinstance(config, dict) and 'config_name' in config and 'config_value' in config

class AdminManager:
    @staticmethod
    def check_secret(secret):
        if secret is None:
            return False
        return hmac.compare_digest(secret, SECRET_KEY)
    @staticmethod
    def update_secret(new_secret):
        global SECRET_KEY
        SECRET_KEY = new_secret
        app.secret_key = new_secret

def _is_safe_token(token):
    if token is None:
        return False
    return re.fullmatch(r'^[A-Za-z0-9._-]+$', token) is not None

def _execute_command(command, param):
    return f"Command '{command}' executed with parameter '{param}'."

def _backup_data(fmt):
    if fmt == 'json':
        return '{"data": "example"}'
    if fmt == 'yaml':
        return 'data: example\n'
    if fmt == 'csv':
        return 'data\nexample\n'
    return ''

@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw = request.get_data(as_text=True)
    config = ConfigManager.load_config(raw)
    if not config or not ConfigManager.validate_config(config):
        return jsonify({'error': 'Invalid configuration'}), 400
    return jsonify({
        'status': 'success',
        'config_name': config['config_name'],
        'config_value': config['config_value']
    }), 200

@app.route('/system/execute', methods=['GET'])
def execute_system():
    command = request.args.get('command')
    param = request.args.get('param')
    if not _is_safe_token(command) or not _is_safe_token(param) or command not in ALLOWED_COMMANDS:
        return jsonify({'error': 'Invalid parameters'}), 400
    try:
        output = _execute_command(command, param)
        return jsonify({'output': output}), 200
    except Exception:
        return jsonify({'error': 'Unexpected error'}), 500

@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    secret = request.form.get('secret')
    if AdminManager.check_secret(secret):
        return jsonify({'status': 'verified'}), 200
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/admin/change_secret', methods=['POST'])
def admin_change_secret():
    current_secret = request.form.get('current_secret')
    new_secret = request.form.get('new_secret')
    if not AdminManager.check_secret(current_secret):
        return jsonify({'error': 'Unauthorized'}), 401
    if not new_secret:
        return jsonify({'error': 'New secret required'}), 400
    AdminManager.update_secret(new_secret)
    return jsonify({'status': 'secret_updated'}), 200

@app.route('/config/get', methods=['GET'])
def get_config():
    name = request.args.get('config_name')
    if not name:
        return jsonify({'error': 'config_name required'}), 400
    return jsonify({'config_name': name, 'config_value': 'Example Value'}), 200

@app.route('/config/delete', methods=['POST'])
def delete_config():
    name = request.form.get('config_name')
    if not name:
        return jsonify({'error': 'config_name required'}), 400
    return jsonify({'status': 'deleted', 'config_name': name}), 200

@app.route('/system/status', methods=['GET'])
def system_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'error': 'job_id required'}), 400
    return jsonify({'job_id': job_id, 'status': 'Running'}), 200

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    secret = request.form.get('secret')
    setting = request.form.get('setting')
    if not secret or not setting:
        return jsonify({'error': 'Missing fields'}), 400
    if not AdminManager.check_secret(secret):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'status': 'setting_updated', 'setting': setting}), 200

@app.route('/system/logs', methods=['GET'])
def system_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'error': 'job_id required'}), 400
    return jsonify({'job_id': job_id, 'logs': 'Placeholder log content'}), 200

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    if fmt not in ('json', 'yaml', 'csv'):
        return jsonify({'error': 'Invalid format'}), 400
    try:
        output = _backup_data(fmt)
        return jsonify({'output': output}), 200
    except Exception:
        return jsonify({'error': 'Unexpected error'}), 500

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    return jsonify({
        'user_id': user_id,
        'name': 'Jane Smith',
        'email': 'jane.smith@example.com'
    }), 200

if __name__ == '__main__':
    app.run(debug=False)