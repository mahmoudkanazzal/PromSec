from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import re

app = Flask(__name__)

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD environment variable not set")

def is_safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

def is_allowed_format(fmt: str) -> bool:
    return fmt in ("json", "csv", "xml")

@app.route('/config/add', methods=['POST'])
def config_add():
    try:
        data = yaml.safe_load(request.data.decode('utf-8'))
    except Exception:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    config_id = data.get('config_id') if isinstance(data, dict) else None
    config_value = data.get('config_value') if isinstance(data, dict) else None
    if not config_id or not config_value:
        return jsonify({"status": "Error", "message": "Missing configuration information"}), 400
    return jsonify({"status": "Configuration added", "config_id": config_id, "config_value": config_value})

@app.route('/job/execute', methods=['GET'])
def job_execute():
    job_name = request.args.get('job_name')
    parameter = request.args.get('parameter')
    if not job_name or not parameter or not is_safe_identifier(job_name) or not is_safe_identifier(parameter):
        return jsonify({"status": "Error", "message": "Invalid job name or parameter"}), 400
    subprocess.run(['sh', 'execute_job.sh', job_name, parameter], check=False)
    return jsonify({"status": "Job execution started"})

@app.route('/auth/login', methods=['POST'])
def auth_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        return jsonify({"status": "Login successful"})
    return jsonify({"status": "Login failed"}), 401

@app.route('/auth/update_password', methods=['POST'])
def auth_update_password():
    global ADMIN_PASSWORD
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({"status": "Login failed"}), 401
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({"status": "Error", "message": "Invalid new password"}), 400
    ADMIN_PASSWORD = new_password
    return jsonify({"status": "Password updated"})

@app.route('/config/get', methods=['GET'])
def config_get():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400
    return jsonify({"status": "Configuration retrieved", "config": {"config_id": config_id, "config_value": "Sample Value"}})

@app.route('/config/remove', methods=['POST'])
def config_remove():
    config_id = request.form.get('config_id')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400
    return jsonify({"status": "Configuration removed", "config_id": config_id})

@app.route('/job/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400
    return jsonify({"status": "Job status", "job_id": job_id, "status": "In Progress"})

@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400
    return jsonify({"status": "Setting updated", "setting": setting})

@app.route('/job/logs', methods=['GET'])
def job_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400
    logs = "Logs for job " + job_id
    return jsonify({"status": "Job logs", "job_id": job_id, "logs": logs})

@app.route('/data/export', methods=['GET'])
def data_export():
    fmt = request.args.get('format', 'json')
    if not is_allowed_format(fmt):
        return jsonify({"status": "Error", "message": "Unsupported export format"}), 400
    subprocess.run(['python', 'export_data.py', fmt], check=False)
    return jsonify({"status": "Data export started"})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    return jsonify({"status": "User information retrieved", "user_info": {"user_id": user_id, "name": "John Doe", "email": "john.doe@example.com"}})

if __name__ == "__main__":
    app.run(debug=False)