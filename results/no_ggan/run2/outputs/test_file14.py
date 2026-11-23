import os
import hashlib
import hmac
import threading
import subprocess
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode('utf-8')).hexdigest()

_SECRET_LOCK = threading.Lock()
_SECRET_HASH = _hash_secret(os.getenv('SECRET_KEY', 'super_secret_key_2024'))

class ConfigManager:
    @staticmethod
    def load_config(yaml_data: str):
        try:
            return yaml.safe_load(yaml_data)
        except yaml.YAMLError:
            return None

    @staticmethod
    def validate_config(config):
        return isinstance(config, dict) and 'config_name' in config and 'config_value' in config

class AdminManager:
    @staticmethod
    def check_secret(secret: str) -> bool:
        provided_hash = _hash_secret(secret)
        with _SECRET_LOCK:
            return hmac.compare_digest(provided_hash, _SECRET_HASH)

    @staticmethod
    def update_secret(new_secret: str):
        global _SECRET_HASH
        new_hash = _hash_secret(new_secret)
        with _SECRET_LOCK:
            _SECRET_HASH = new_hash

@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw = request.get_data(as_text=True)
    config = ConfigManager.load_config(raw)
    if not ConfigManager.validate_config(config):
        return jsonify({'error': 'Invalid configuration'}), 400
    return jsonify({
        'status': 'Configuration uploaded',
        'config_name': config['config_name'],
        'config_value': config['config_value']
    })

@app.route('/system/execute', methods=['GET'])
def system_execute():
    command = request.args.get('command')
    param = request.args.get('param')
    if not command or not param:
        return jsonify({'error': 'Missing parameters'}), 400
    try:
        subprocess.run(['./execute_script.sh', command, param],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Execution failed'}), 500
    return jsonify({'status': 'System execution started'})

@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    secret = request.form.get('secret', '')
    if AdminManager.check_secret(secret):
        return jsonify({'status': 'Verification successful'})
    return jsonify({'status': 'Verification failed'}), 401

@app.route('/admin/change_secret', methods=['POST'])
def admin_change_secret():
    current = request.form.get('current_secret', '')
    new = request.form.get('new_secret', '')
    if not AdminManager.check_secret(current) or not new:
        return jsonify({'status': 'Verification failed'}), 401
    AdminManager.update_secret(new)
    return jsonify({'status': 'Secret changed successfully'})

@app.route('/config/get', methods=['GET'])
def config_get():
    name = request.args.get('config_name')
    if not name:
        return jsonify({'error': 'Missing config_name'}), 400
    return jsonify({
        'status': 'Configuration retrieved',
        'config': {
            'config_name': name,
            'config_value': 'Example Value'
        }
    })

@app.route('/config/delete', methods=['POST'])
def config_delete():
    name = request.form.get('config_name')
    if not name:
        return jsonify({'error': 'Missing config_name'}), 400
    return jsonify({'status': 'Configuration deleted', 'config_name': name})

@app.route('/system/status', methods=['GET'])
def system_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'error': 'Missing job_id'}), 400
    return jsonify({
        'status': 'System status',
        'job_id': job_id,
        'status_detail': 'Running'
    })

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    secret = request.form.get('secret', '')
    setting = request.form.get('setting')
    if not AdminManager.check_secret(secret):
        return jsonify({'status': 'Verification failed'}), 401
    if setting is None:
        return jsonify({'error': 'Missing setting'}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting})

@app.route('/system/logs', methods=['GET'])
def system_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'error': 'Missing job_id'}), 400
    return jsonify({
        'status': 'System logs',
        'job_id': job_id,
        'logs': f'Sample logs for job {job_id}'
    })

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    if fmt not in ('json', 'yaml', 'csv'):
        return jsonify({'error': 'Invalid format'}), 400
    try:
        subprocess.run(['python3', 'backup_data.py', fmt],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Backup failed'}), 500
    return jsonify({'status': 'Data backup started'})

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    return jsonify({
        'status': 'User details retrieved',
        'user': {
            'user_id': user_id,
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com'
        }
    })

if __name__ == '__main__':
    app.run(debug=False)