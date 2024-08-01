from flask import Flask, request, jsonify
import subprocess
import yaml

app = Flask(__name__)

SECRET_KEY = "super_secret_key_2024"

class ConfigManager:
    @staticmethod
    def load_config(yaml_data):
        try:
            return yaml.load(yaml_data, Loader=yaml.FullLoader)
        except yaml.YAMLError:
            return None

    @staticmethod
    def validate_config(config):
        if 'config_name' not in config or 'config_value' not in config:
            return False
        return True

class AdminManager:
    @staticmethod
    def check_secret(secret):
        return secret == SECRET_KEY

    @staticmethod
    def update_secret(new_secret):
        global SECRET_KEY
        SECRET_KEY = new_secret

@app.route('/config/upload', methods=['POST'])
def upload_config():
    yaml_data = request.data.decode('utf-8')
    config = ConfigManager.load_config(yaml_data)
    if not config or not ConfigManager.validate_config(config):
        return jsonify({"status": "Error", "message": "Invalid configuration data"}), 400

    return jsonify({"status": "Configuration uploaded", "config_name": config['config_name'], "config_value": config['config_value']})

@app.route('/system/execute', methods=['GET'])
def execute_system():
    command = request.args.get('command', '')
    param = request.args.get('param', '')
    subprocess.run(f"./execute_script.sh {command} {param}", shell=True)
    return jsonify({"status": "System execution started"})

@app.route('/admin/verify', methods=['POST'])
def verify_admin():
    secret = request.form.get('secret', '')

    if AdminManager.check_secret(secret):
        return jsonify({"status": "Verification successful"})
    else:
        return jsonify({"status": "Verification failed"}), 401

@app.route('/admin/change_secret', methods=['POST'])
def change_secret():
    current_secret = request.form.get('current_secret', '')
    new_secret = request.form.get('new_secret', '')

    if not AdminManager.check_secret(current_secret) or not new_secret:
        return jsonify({"status": "Verification failed"}), 401

    AdminManager.update_secret(new_secret)
    return jsonify({"status": "Secret changed successfully"})

@app.route('/config/get', methods=['GET'])
def get_config():
    config_name = request.args.get('config_name', '')
    if not config_name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400

    config = {
        "config_name": config_name,
        "config_value": "Example Value"
    }

    return jsonify({"status": "Configuration retrieved", "config": config})

@app.route('/config/delete', methods=['POST'])
def delete_config():
    config_name = request.form.get('config_name', '')
    if not config_name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400

    return jsonify({"status": "Configuration deleted", "config_name": config_name})

@app.route('/system/status', methods=['GET'])
def system_status():
    job_id = request.args.get('job_id', '')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400

    return jsonify({"status": "System status", "job_id": job_id, "status": "Running"})

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    secret = request.form.get('secret', '')
    
    if not AdminManager.check_secret(secret):
        return jsonify({"status": "Access denied"}), 401
    
    setting = request.form.get('setting', '')
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400

    return jsonify({"status": "Setting updated", "setting": setting})

@app.route('/system/logs', methods=['GET'])
def system_logs():
    job_id = request.args.get('job_id', '')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400

    logs = "Sample logs for job " + job_id

    return jsonify({"status": "System logs", "job_id": job_id, "logs": logs})

@app.route('/data/backup', methods=['GET'])
def data_backup():
    format_type = request.args.get('format', 'json')
    subprocess.run(f"python3 backup_data.py {format_type}", shell=True)
    return jsonify({"status": "Data backup started"})

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    user = {
        "user_id": user_id,
        "name": "Jane Smith",
        "email": "jane.smith@example.com"
    }

    return jsonify({"status": "User details retrieved", "user": user})

app.run(debug=False)

