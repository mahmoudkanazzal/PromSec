from flask import Flask, request, jsonify
import subprocess
import yaml
import os
import re

app = Flask(__name__)
admin_password = os.getenv('ADMIN_PASSWORD', 'admin_pass_2024')

def validate_yaml(data):
    try:
        return yaml.safe_load(data)
    except Exception:
        return None

def _is_safe_token(value):
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

@app.route('/config/upload', methods=['POST'])
def config_upload():
    raw = request.get_data(as_text=True)
    parsed = validate_yaml(raw)
    if not isinstance(parsed, dict) or 'config_name' not in parsed or 'config_value' not in parsed:
        return jsonify({"status": "Error", "message": "Invalid YAML data"}), 400
    return jsonify({
        "status": "Configuration uploaded",
        "config_name": parsed['config_name'],
        "config_value": parsed['config_value']
    })

@app.route('/service/execute', methods=['GET'])
def service_execute():
    service = request.args.get('service')
    param = request.args.get('param')
    if not service or not param or not _is_safe_token(service) or not _is_safe_token(param):
        return jsonify({"status": "Error", "message": "Invalid service or parameter"}), 400
    subprocess.run(["bash", "run_service.sh", service, param], check=False)
    return jsonify({"status": "Service execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == admin_password:
        return jsonify({"status": "Login successful"})
    return jsonify({"status": "Login failed"}), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global admin_password
    current = request.form.get('current_password')
    new = request.form.get('new_password')
    if current != admin_password:
        return jsonify({"status": "Access denied"}), 401
    if not new:
        return jsonify({"status": "Error", "message": "New password is required"}), 400
    admin_password = new
    return jsonify({"status": "Password updated"})

@app.route('/config/retrieve', methods=['GET'])
def config_retrieve():
    config_name = request.args.get('config_name')
    if not config_name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400
    return jsonify({
        "status": "Configuration retrieved",
        "config": {"config_name": config_name, "config_value": "Sample Config Value"}
    })

@app.route('/config/delete', methods=['POST'])
def config_delete():
    config_name = request.form.get('config_name')
    if not config_name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400
    return jsonify({"status": "Configuration deleted", "config_name": config_name})

@app.route('/service/status', methods=['GET'])
def service_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400
    return jsonify({"status": "Service status", "job_id": job_id, "status": "Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    setting = request.form.get('setting')
    if password != admin_password:
        return jsonify({"status": "Access denied"}), 401
    if not setting:
        return jsonify({"status": "Error", "message": "Setting is required"}), 400
    return jsonify({"status": "Setting updated", "setting": setting})

@app.route('/service/logs', methods=['GET'])
def service_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400
    return jsonify({"status": "Service logs", "job_id": job_id, "logs": "Sample logs for job " + job_id})

@app.route('/backup/data', methods=['GET'])
def backup_data():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ('json', 'yaml'):
        return jsonify({"status": "Error", "message": "Invalid backup format"}), 400
    subprocess.run(["python3", "backup_data.py", fmt], check=False)
    return jsonify({"status": "Data backup started"})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    return jsonify({
        "status": "User information retrieved",
        "user": {"user_id": user_id, "name": "Samuel Green", "email": "samuel.green@example.com"}
    })

if __name__ == "__main__":
    app.run(debug=False)