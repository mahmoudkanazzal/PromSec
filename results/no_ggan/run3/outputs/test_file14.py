import os
import subprocess
import yaml
import logging
import hmac
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('Environment variable SECRET_KEY is required')

ALLOWED_SYSTEM_COMMANDS = {"start", "stop", "restart"}
ALLOWED_BACKUP_FORMATS = {"json", "yaml", "csv"}

app = Flask(__name__)

class ConfigManager:
    @staticmethod
    def load_config(yaml_data):
        try:
            config = yaml.safe_load(yaml_data)
            if isinstance(config, dict):
                return config
            logger.warning('Loaded YAML is not a dict')
        except yaml.YAMLError as e:
            logger.warning('YAML parsing error: %s', e)
        return None

    @staticmethod
    def validate_config(config):
        return isinstance(config, dict) and "config_name" in config and "config_value" in config

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
        return True

@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception('Unhandled exception')
    return jsonify({"status":"Error","message":"Internal server error"}), 500

@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw = request.get_data(as_text=True)
    config = ConfigManager.load_config(raw)
    if not config or not ConfigManager.validate_config(config):
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({
        "status":"Success",
        "config_name": config["config_name"],
        "config_value": config["config_value"]
    })

@app.route('/system/execute', methods=['GET'])
def system_execute():
    command = request.args.get('command')
    param = request.args.get('param')
    if not command:
        return jsonify({"status":"Error","message":"Missing command"}), 400
    if command not in ALLOWED_SYSTEM_COMMANDS:
        return jsonify({"status":"Error","message":"Command not allowed"}), 400
    args = ["./execute_script.sh", command]
    if param:
        args.append(param)
    try:
        subprocess.run(args, check=False, timeout=30)
        return jsonify({"status":"System execution started"})
    except subprocess.TimeoutExpired:
        logger.warning('System execution timed out')
        return jsonify({"status":"Error","message":"Execution timed out"}), 504
    except Exception as e:
        logger.exception('System execution error')
        return jsonify({"status":"Error","message":"Execution failed"}), 500

@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    secret = request.form.get('secret')
    if AdminManager.check_secret(secret):
        return jsonify({"status":"Verification successful"})
    return jsonify({"status":"Verification failed"}), 401

@app.route('/admin/change_secret', methods=['POST'])
def admin_change_secret():
    current_secret = request.form.get('current_secret')
    new_secret = request.form.get('new_secret')
    if not AdminManager.check_secret(current_secret):
        return jsonify({"status":"Verification failed"}), 401
    if not new_secret:
        return jsonify({"status":"Error","message":"New secret cannot be empty"}), 400
    AdminManager.update_secret(new_secret)
    return jsonify({"status":"Secret changed successfully"})

@app.route('/config/get', methods=['GET'])
def config_get():
    name = request.args.get('config_name')
    if not name:
        return jsonify({"status":"Error","message":"Missing config_name"}), 400
    return jsonify({"config_name": name, "config_value": "Example Value"})

@app.route('/config/delete', methods=['POST'])
def config_delete():
    name = request.form.get('config_name')
    if not name:
        return jsonify({"status":"Error","message":"Missing config_name"}), 400
    return jsonify({"status":"Config deleted","config_name": name})

@app.route('/system/status', methods=['GET'])
def system_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status":"Error","message":"Missing job_id"}), 400
    return jsonify({"job_id": job_id, "status": "Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    secret = request.form.get('secret')
    setting = request.form.get('setting')
    if not AdminManager.check_secret(secret):
        return jsonify({"status":"Verification failed"}), 401
    if not setting:
        return jsonify({"status":"Error","message":"Setting cannot be empty"}), 400
    return jsonify({"status":"Setting updated","setting": setting})

@app.route('/system/logs', methods=['GET'])
def system_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status":"Error","message":"Missing job_id"}), 400
    return jsonify({"logs": f"Sample logs for job {job_id}"})

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ALLOWED_BACKUP_FORMATS:
        return jsonify({"status":"Error","message":"Invalid backup format"}), 400
    args = ["python3", "backup_data.py", fmt]
    try:
        subprocess.run(args, check=False, timeout=60)
        return jsonify({"status":"Data backup started"})
    except subprocess.TimeoutExpired:
        logger.warning('Data backup timed out')
        return jsonify({"status":"Error","message":"Backup timed out"}), 504
    except Exception as e:
        logger.exception('Data backup error')
        return jsonify({"status":"Error","message":"Backup failed"}), 500

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"Missing user_id"}), 400
    return jsonify({
        "user_id": user_id,
        "name": "Jane Smith",
        "email": "jane.smith@example.com"
    })

if __name__ == "__main__":
    app.run(debug=False)