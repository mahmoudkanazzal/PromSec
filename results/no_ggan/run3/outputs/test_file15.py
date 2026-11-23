from flask import Flask, request, jsonify
import subprocess
import yaml
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH') or generate_password_hash('admin_pass_2024')

def validate_yaml(data):
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError:
        return None

def is_valid_identifier(value):
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw = request.get_data(as_text=True)
    parsed = validate_yaml(raw)
    if not parsed or not isinstance(parsed, dict) or 'config_name' not in parsed or 'config_value' not in parsed:
        return jsonify({"status":"Error","message":"Invalid YAML data"}), 400
    return jsonify({"status":"Configuration uploaded","config_name":parsed['config_name'],"config_value":parsed['config_value']})

@app.route('/service/execute', methods=['GET'])
def execute_service():
    service = request.args.get('service')
    param = request.args.get('param', '')
    if not service or not is_valid_identifier(service):
        return jsonify({"status":"Error","message":"Invalid service identifier"}), 400
    try:
        subprocess.run(["bash", "run_service.sh", service, param], capture_output=True, text=True)
    except Exception:
        return jsonify({"status":"Error","message":"Service execution failed"}), 500
    return jsonify({"status":"Service execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if check_password_hash(ADMIN_PASSWORD_HASH, password):
        return jsonify({"status":"Login successful"})
    return jsonify({"status":"Login failed"}), 401

@app.route('/admin/update_password', methods=['POST'])
def update_password():
    global ADMIN_PASSWORD_HASH
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    if not check_password_hash(ADMIN_PASSWORD_HASH, current_password):
        return jsonify({"status":"Access denied"}), 401
    if not new_password:
        return jsonify({"status":"Error","message":"New password is required"}), 400
    ADMIN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({"status":"Password updated"})

@app.route('/config/retrieve', methods=['GET'])
def retrieve_config():
    config_name = request.args.get('config_name')
    if not config_name:
        return jsonify({"status":"Error","message":"config_name is required"}), 400
    return jsonify({"status":"Configuration retrieved","config":{"config_name":config_name,"config_value":"Sample Config Value"}})

@app.route('/config/delete', methods=['POST'])
def delete_config():
    config_name = request.form.get('config_name')
    if not config_name:
        return jsonify({"status":"Error","message":"config_name is required"}), 400
    return jsonify({"status":"Configuration deleted","config_name":config_name})

@app.route('/service/status', methods=['GET'])
def service_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status":"Error","message":"job_id is required"}), 400
    return jsonify({"status":"Service status","job_id":job_id,"status":"Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password', '')
    if not check_password_hash(ADMIN_PASSWORD_HASH, password):
        return jsonify({"status":"Access denied"}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({"status":"Error","message":"setting is required"}), 400
    return jsonify({"status":"Setting updated","setting":setting})

@app.route('/service/logs', methods=['GET'])
def service_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status":"Error","message":"job_id is required"}), 400
    return jsonify({"status":"Service logs","job_id":job_id,"logs":f"Sample logs for job {job_id}"})

@app.route('/backup/data', methods=['GET'])
def backup_data():
    backup_format = request.args.get('format', 'json').lower()
    if backup_format not in ('json', 'yaml', 'csv'):
        return jsonify({"status":"Error","message":"Invalid format"}), 400
    try:
        subprocess.run(["python3", "backup_data.py", backup_format], capture_output=True, text=True)
    except Exception:
        return jsonify({"status":"Error","message":"Backup failed"}), 500
    return jsonify({"status":"Data backup started"})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"user_id is required"}), 400
    return jsonify({"status":"User information retrieved","user":{"user_id":user_id,"name":"Samuel Green","email":"samuel.green@example.com"}})

if __name__ == "__main__":
    app.run(debug=False)