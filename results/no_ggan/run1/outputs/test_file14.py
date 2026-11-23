import os
import hashlib
import hmac
import subprocess
from flask import Flask, request, jsonify, make_response
import yaml

def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()

ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'default_admin_secret')
SECRET_HASH = _hash_secret(ADMIN_SECRET)

def verify_secret(secret: str) -> bool:
    return hmac.compare_digest(_hash_secret(secret), SECRET_HASH)

app = Flask(__name__)

class ConfigManager:
    @staticmethod
    def load_config(yaml_data: str):
        try:
            return yaml.safe_load(yaml_data)
        except yaml.YAMLError:
            return None

    @staticmethod
    def validate_config(config):
        if not isinstance(config, dict):
            return False
        return 'config_name' in config and 'config_value' in config

class AdminManager:
    @staticmethod
    def _hash_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()

    @staticmethod
    def check_secret(secret: str) -> bool:
        return hmac.compare_digest(AdminManager._hash_secret(secret), SECRET_HASH)

    @staticmethod
    def update_secret(new_secret: str):
        global SECRET_HASH
        SECRET_HASH = AdminManager._hash_secret(new_secret)

@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw_data = request.get_data(as_text=True)
    config = ConfigManager.load_config(raw_data)
    if config is None or not ConfigManager.validate_config(config):
        return make_response(jsonify({"status": "Error", "message": "Invalid configuration data"}), 400)
    return jsonify({
        "status": "Success",
        "config_name": config["config_name"],
        "config_value": config["config_value"]
    })

@app.route('/system/execute', methods=['GET'])
def system_execute():
    command = request.args.get('command')
    param = request.args.get('param', '')
    if not command:
        return make_response(jsonify({"status": "Error", "message": "Missing command parameter"}), 400)
    try:
        subprocess.run(['./execute_script.sh', command, param], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({"status": "System execution started"})
    except Exception:
        return make_response(jsonify({"status": "Error", "message": "Execution failed"}), 500)

@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    secret = request.form.get('secret', '')
    if AdminManager.check_secret(secret):
        return jsonify({"status": "Verification successful"})
    return make_response(jsonify({"status": "Verification failed"}), 401)

@app.route('/admin/change_secret', methods=['POST'])
def admin_change_secret():
    current_secret = request.form.get('current_secret', '')
    new_secret = request.form.get('new_secret', '')
    if not AdminManager.check_secret(current_secret) or not new_secret:
        return make_response(jsonify({"status": "Error", "message": "Invalid credentials or empty new secret"}), 401)
    AdminManager.update_secret(new_secret)
    return jsonify({"status": "Secret changed successfully"})

@app.route('/config/get', methods=['GET'])
def get_config():
    config_name = request.args.get('config_name')
    if not config_name:
        return make_response(jsonify({"status": "Error", "message": "Missing config_name parameter"}), 400)
    return jsonify({
        "status": "Success",
        "config": {
            "config_name": config_name,
            "config_value": "Example Value"
        }
    })

@app.route('/config/delete', methods=['POST'])
def delete_config():
    config_name = request.form.get('config_name')
    if not config_name:
        return make_response(jsonify({"status": "Error", "message": "Missing config_name field"}), 400)
    return jsonify({"status": "Configuration deleted", "config_name": config_name})

@app.route('/system/status', methods=['GET'])
def system_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return make_response(jsonify({"status": "Error", "message": "Missing job_id parameter"}), 400)
    return jsonify({
        "status": "System status",
        "job_id": job_id,
        "system_status": "Running"
    })

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    secret = request.form.get('secret', '')
    if not AdminManager.check_secret(secret):
        return make_response(jsonify({"status": "Access denied"}), 401)
    setting = request.form.get('setting')
    if setting is None:
        return make_response(jsonify({"status": "Error", "message": "Missing setting field"}), 400)
    return jsonify({"status": "Setting updated", "setting": setting})

@app.route('/system/logs', methods=['GET'])
def system_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return make_response(jsonify({"status": "Error", "message": "Missing job_id parameter"}), 400)
    return jsonify({
        "status": "System logs",
        "job_id": job_id,
        "logs": f"Sample logs for job {job_id}"
    })

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    if fmt not in ('json', 'yaml', 'csv'):
        return make_response(jsonify({"status": "Error", "message": "Invalid format"}), 400)
    try:
        subprocess.run(['python3', 'backup_data.py', fmt], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({"status": "Data backup started"})
    except Exception:
        return make_response(jsonify({"status": "Error", "message": "Backup failed"}), 500)

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('user_id')
    if not user_id:
        return make_response(jsonify({"status": "Error", "message": "Missing user_id parameter"}), 400)
    return jsonify({
        "status": "User details retrieved",
        "user": {
            "user_id": user_id,
            "name": "Jane Smith",
            "email": "jane.smith@example.com"
        }
    })

if __name__ == '__main__':
    app.run(debug=False)