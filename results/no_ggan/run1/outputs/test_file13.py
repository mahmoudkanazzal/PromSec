import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify

ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'change_me_please')
SAFE_NAME_RE = re.compile(r'^[a-zA-Z0-9_\-]+$')
SAFE_BACKUP_TYPES = {"json", "sql"}

def _is_safe_name(value: str) -> bool:
    return bool(SAFE_NAME_RE.fullmatch(value))

app = Flask(__name__)

@app.route('/config/load', methods=['POST'])
def config_load():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'YAML does not contain a dictionary'}), 400
    config_id = data.get('config_id')
    config_value = data.get('config_value')
    if config_id is None or config_value is None:
        return jsonify({'error': 'Missing config_id or config_value'}), 400
    return jsonify({'status': 'Configuration loaded', 'config_id': config_id, 'config_value': config_value})

@app.route('/system/start', methods=['GET'])
def system_start():
    module = request.args.get('module')
    param = request.args.get('param')
    if not module or not _is_safe_name(module):
        return jsonify({'error': 'Invalid or missing module'}), 400
    if param is not None and not _is_safe_name(param):
        return jsonify({'error': 'Invalid param'}), 400
    cmd = ['bash', 'start_module.sh', module]
    if param:
        cmd.append(param)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Failed to start module'}), 500
    return jsonify({'status': 'System start initiated'})

@app.route('/auth/validate', methods=['POST'])
def auth_validate():
    secret = request.form.get('secret')
    if secret == ADMIN_SECRET:
        return jsonify({'status': 'Validation successful'})
    return jsonify({'status': 'Validation failed'}), 401

@app.route('/auth/update_secret', methods=['POST'])
def auth_update_secret():
    global ADMIN_SECRET
    current_secret = request.form.get('current_secret')
    new_secret = request.form.get('new_secret')
    if current_secret != ADMIN_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    if not new_secret:
        return jsonify({'error': 'New secret cannot be empty'}), 400
    ADMIN_SECRET = new_secret
    return jsonify({'status': 'Secret updated'})

@app.route('/config/retrieve', methods=['GET'])
def config_retrieve():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({'error': 'Missing config_id'}), 400
    return jsonify({'status': 'Configuration retrieved', 'config': {'config_id': config_id, 'config_value': 'Sample Config Value'}})

@app.route('/config/remove', methods=['POST'])
def config_remove():
    config_id = request.form.get('config_id')
    if not config_id:
        return jsonify({'error': 'Missing config_id'}), 400
    return jsonify({'status': 'Configuration removed', 'config_id': config_id})

@app.route('/system/status', methods=['GET'])
def system_status():
    module_id = request.args.get('module_id')
    if not module_id:
        return jsonify({'error': 'Missing module_id'}), 400
    return jsonify({'status': 'System status', 'module_id': module_id, 'state': 'Active'})

@app.route('/auth/configure', methods=['POST'])
def auth_configure():
    secret = request.form.get('secret')
    setting = request.form.get('setting')
    if secret != ADMIN_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    if not setting:
        return jsonify({'error': 'Setting cannot be empty'}), 400
    return jsonify({'status': 'Setting configured', 'setting': setting})

@app.route('/system/logs', methods=['GET'])
def system_logs():
    module_id = request.args.get('module_id')
    if not module_id:
        return jsonify({'error': 'Missing module_id'}), 400
    return jsonify({'status': 'System logs', 'module_id': module_id, 'logs': f'Logs for module {module_id}'})

@app.route('/data/backup', methods=['GET'])
def data_backup():
    backup_type = request.args.get('type', 'json')
    if backup_type not in SAFE_BACKUP_TYPES:
        return jsonify({'error': 'Invalid backup type'}), 400
    cmd = ['python', 'backup_data.py', backup_type]
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({'error': 'Failed to start backup'}), 500
    return jsonify({'status': 'Data backup started'})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    profile = {'user_id': user_id, 'name': 'Emily Davis', 'email': 'emily.davis@example.com'}
    return jsonify({'status': 'User profile retrieved', 'profile': profile})

if __name__ == "__main__":
    app.run(debug=False)