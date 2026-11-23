import os
import secrets
import yaml
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
_secret_key = os.getenv('SECRET_KEY')
if not _secret_key:
    _secret_key = secrets.token_hex(24)
app.secret_key = _secret_key

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
    _secret = _secret_key
    @staticmethod
    def check_secret(secret):
        return secret == AdminManager._secret
    @staticmethod
    def update_secret(new_secret):
        AdminManager._secret = new_secret

@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw = request.get_data(as_text=True)
    cfg = ConfigManager.load_config(raw)
    if cfg and ConfigManager.validate_config(cfg):
        return jsonify({
            'status': 'Configuration uploaded',
            'config_name': cfg['config_name'],
            'config_value': cfg['config_value']
        }), 200
    return jsonify({'status': 'Error', 'message': 'Invalid configuration data'}), 400

@app.route('/system/execute', methods=['GET'])
def system_execute():
    command = request.args.get('command', '')
    param = request.args.get('param', '')
    subprocess.run(['./execute_script.sh', command, param], check=False)
    return jsonify({'status': 'System execution started'})

@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    secret = request.form.get('secret', '')
    if AdminManager.check_secret(secret):
        return jsonify({'status': 'Verification successful'})
    return jsonify({'status': 'Verification failed'}), 401

@app.route('/admin/change_secret', methods=['POST'])
def change_secret():
    current = request.form.get('current_secret', '')
    new = request.form.get('new_secret', '')
    if AdminManager.check_secret(current) and new:
        AdminManager.update_secret(new)
        return jsonify({'status': 'Secret changed successfully'})
    return jsonify({'status': 'Verification failed'}), 401

@app.route('/config/get', methods=['GET'])
def get_config():
    name = request.args.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'Configuration name is required'}), 400
    return jsonify({
        'status': 'Configuration retrieved',
        'config': {'config_name': name, 'config_value': 'Example Value'}
    })

@app.route('/config/delete', methods=['POST'])
def delete_config():
    name = request.form.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'Configuration name is required'}), 400
    return jsonify({'status': 'Configuration deleted', 'config_name': name})

@app.route('/system/status', methods=['GET'])
def system_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Job ID is required'}), 400
    return jsonify({'status': 'System status', 'job_id': job_id, 'status': 'Running'})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    secret = request.form.get('secret', '')
    if not AdminManager.check_secret(secret):
        return jsonify({'status': 'Access denied'}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({'status': 'Error', 'message': 'Invalid setting'}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting})

@app.route('/system/logs', methods=['GET'])
def system_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Job ID is required'}), 400
    return jsonify({'status': 'System logs', 'job_id': job_id, 'logs': 'Sample logs for job ' + job_id})

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    subprocess.run(['python3', 'backup_data.py', fmt], check=False)
    return jsonify({'status': 'Data backup started'})

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'User ID is required'}), 400
    return jsonify({
        'status': 'User details retrieved',
        'user': {'user_id': user_id, 'name': 'Jane Smith', 'email': 'jane.smith@example.com'}
    })

if __name__ == '__main__':
    app.run(debug=False)