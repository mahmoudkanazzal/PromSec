import os
import re
import subprocess
import threading
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'admin_secret_2024')
_secret_lock = threading.Lock()
SAFE_NAME_RE = re.compile(r'^[\w\-]+$')
ALLOWED_BACKUP_TYPES = {'json', 'csv', 'xml'}

@app.route('/config/load', methods=['POST'])
def load_config():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"YAML must define a mapping"}), 400
    config_id = data.get('config_id')
    config_value = data.get('config_value')
    if not config_id or not config_value:
        return jsonify({"status":"Error","message":"Missing configuration information"}), 400
    return jsonify({"status":"Configuration loaded","config_id":config_id,"config_value":config_value}), 200

@app.route('/system/start', methods=['GET'])
def system_start():
    module = request.args.get('module')
    param = request.args.get('param')
    if not module or not SAFE_NAME_RE.fullmatch(module):
        return jsonify({"status":"Error","message":"Invalid or missing module name"}), 400
    if param is not None and not SAFE_NAME_RE.fullmatch(param):
        return jsonify({"status":"Error","message":"Invalid param value"}), 400
    script_path = os.path.abspath(os.path.join(os.getcwd(), 'start_module.sh'))
    cmd = ['bash', script_path, module]
    if param:
        cmd.append(param)
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        return jsonify({"status":"Error","message":f"Failed to start module: {e}"}), 500
    return jsonify({"status":"System start initiated"}), 200

@app.route('/auth/validate', methods=['POST'])
def auth_validate():
    secret = request.form.get('secret')
    if secret == ADMIN_SECRET:
        return jsonify({"status":"Validation successful"}), 200
    return jsonify({"status":"Validation failed"}), 401

@app.route('/auth/update_secret', methods=['POST'])
def auth_update_secret():
    global ADMIN_SECRET
    current_secret = request.form.get('current_secret')
    new_secret = request.form.get('new_secret')
    if current_secret != ADMIN_SECRET:
        return jsonify({"status":"Validation failed"}), 401
    if not new_secret:
        return jsonify({"status":"Error","message":"Invalid new secret"}), 400
    with _secret_lock:
        ADMIN_SECRET = new_secret
    return jsonify({"status":"Secret updated"}), 200

@app.route('/config/retrieve', methods=['GET'])
def config_retrieve():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({"status":"Error","message":"Configuration ID is required"}), 400
    return jsonify({"status":"Configuration retrieved","config":{"config_id":config_id,"config_value":"Sample Config Value"}}), 200

@app.route('/config/remove', methods=['POST'])
def config_remove():
    config_id = request.form.get('config_id')
    if not config_id:
        return jsonify({"status":"Error","message":"Configuration ID is required"}), 400
    return jsonify({"status":"Configuration removed","config_id":config_id}), 200

@app.route('/system/status', methods=['GET'])
def system_status():
    module_id = request.args.get('module_id')
    if not module_id:
        return jsonify({"status":"Error","message":"Module ID is required"}), 400
    return jsonify({"status":"System status","module_id":module_id,"system_state":"Active"}), 200

@app.route('/auth/configure', methods=['POST'])
def auth_configure():
    secret = request.form.get('secret')
    setting = request.form.get('setting')
    if secret != ADMIN_SECRET:
        return jsonify({"status":"Access denied"}), 401
    if not setting:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting configured","setting":setting}), 200

@app.route('/system/logs', methods=['GET'])
def system_logs():
    module_id = request.args.get('module_id')
    if not module_id:
        return jsonify({"status":"Error","message":"Module ID is required"}), 400
    logs = f"Logs for module {module_id}"
    return jsonify({"status":"System logs","module_id":module_id,"logs":logs}), 200

@app.route('/data/backup', methods=['GET'])
def data_backup():
    backup_type = request.args.get('type', 'json')
    if backup_type not in ALLOWED_BACKUP_TYPES:
        return jsonify({"status":"Error","message":"Unsupported backup type"}), 400
    script_path = os.path.abspath(os.path.join(os.getcwd(), 'backup_data.py'))
    cmd = ['python', script_path, backup_type]
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        return jsonify({"status":"Error","message":f"Backup failed: {e}"}), 500
    return jsonify({"status":"Data backup started"}), 200

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    profile = {"user_id":user_id,"name":"Emily Davis","email":"emily.davis@example.com"}
    return jsonify({"status":"User profile retrieved","profile":profile}), 200

if __name__ == "__main__":
    app.run(debug=False)