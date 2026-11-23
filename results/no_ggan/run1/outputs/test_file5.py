import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

_ADMIN_PASSWORD_HASH_ENV = os.getenv('ADMIN_PASSWORD_HASH')
if _ADMIN_PASSWORD_HASH_ENV:
    ADMIN_PASSWORD_HASH = _ADMIN_PASSWORD_HASH_ENV
else:
    ADMIN_PASSWORD_HASH = generate_password_hash('admin1234')

def verify_admin_password(password: str) -> bool:
    return check_password_hash(ADMIN_PASSWORD_HASH, password)

ALLOWED_TASKS = {"backup", "cleanup", "report"}
ALLOWED_EXPORT_FORMATS = {"csv", "json"}

@app.route('/data/upload', methods=['POST'])
def data_upload():
    raw = request.get_data(as_text=True)
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(parsed, dict):
        return jsonify({"status":"Error","message":"YAML must represent a mapping"}), 400
    data_id = parsed.get('data_id')
    data_value = parsed.get('data_value')
    if not data_id or not data_value:
        return jsonify({"status":"Error","message":"Missing data information"}), 400
    return jsonify({"status":"Data uploaded","data_id":data_id,"data_value":data_value})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task', '')
    parameter = request.args.get('parameter', '')
    if task not in ALLOWED_TASKS:
        return jsonify({"status":"Error","message":"Invalid task name"}), 400
    if not re.fullmatch(r'^[\w\-.]*$', parameter):
        return jsonify({"status":"Error","message":"Invalid parameter"}), 400
    try:
        subprocess.run(["sh","execute_task.sh",task,parameter], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"status":"Error","message":"Task execution failed"}), 500
    return jsonify({"status":"Task execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if verify_admin_password(password):
        return jsonify({"status":"Access granted"})
    else:
        return jsonify({"status":"Access denied"}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    new_config = request.form.get('new_config', '')
    if not verify_admin_password(password):
        return jsonify({"status":"Access denied"}), 401
    if not new_config:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","new_config":new_config})

@app.route('/data/retrieve', methods=['GET'])
def data_retrieve():
    data_id = request.args.get('data_id', '')
    if not data_id:
        return jsonify({"status":"Error","message":"Data ID is required"}), 400
    return jsonify({"status":"Data retrieved","data_info":{"data_id":data_id,"data_value":"Sample Value"}})

@app.route('/data/delete', methods=['POST'])
def data_delete():
    data_id = request.form.get('data_id', '')
    if not data_id:
        return jsonify({"status":"Error","message":"Data ID is required"}), 400
    return jsonify({"status":"Data deleted","data_id":data_id})

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    return jsonify({"status":"Error","message":"Password change via API is not supported. Update the ADMIN_PASSWORD_HASH environment variable."}), 403

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task status","task_id":task_id,"task_state":"Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password', '')
    new_setting = request.form.get('new_setting', '')
    if not verify_admin_password(password):
        return jsonify({"status":"Access denied"}), 401
    if not new_setting:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting applied","new_setting":new_setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task logs","task_id":task_id,"logs":f"Sample logs for task {task_id}"})

@app.route('/data/export', methods=['GET'])
def data_export():
    export_format = request.args.get('format', 'csv').lower()
    if export_format not in ALLOWED_EXPORT_FORMATS:
        return jsonify({"status":"Error","message":"Unsupported export format"}), 400
    try:
        subprocess.run(["python3","export_data.py",export_format], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"status":"Error","message":"Data export failed"}), 500
    return jsonify({"status":"Data export started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User profile","profile":{"user_id":user_id,"name":"John Doe","email":"john.doe@example.com"}})

if __name__ == "__main__":
    app.run(debug=False)