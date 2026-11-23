from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import re
import hmac

app = Flask(__name__)
SECRET_TOKEN = os.getenv('SECRET_TOKEN', 'secure_token_2024')
SAFE_PARAM_RE = re.compile(r'^[\w\-]+$')
SAFE_FORMATS = {"json", "yaml", "csv"}

@app.route('/config/upload', methods=['POST'])
def config_upload():
    try:
        data = request.data.decode('utf-8')
        parsed = yaml.safe_load(data)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(parsed, dict):
        return jsonify({"status":"Error","message":"YAML must define a mapping"}), 400
    config_name = parsed.get('config_name')
    config_value = parsed.get('config_value')
    if not config_name or not config_value:
        return jsonify({"status":"Error","message":"Missing configuration details"}), 400
    return jsonify({"status":"Configuration uploaded","config_name":config_name,"config_value":config_value})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    param = request.args.get('param')
    if not task or not param:
        return jsonify({"status":"Error","message":"Both task and param are required"}), 400
    if not SAFE_PARAM_RE.fullmatch(task) or not SAFE_PARAM_RE.fullmatch(param):
        return jsonify({"status":"Error","message":"Invalid characters in task or param"}), 400
    try:
        subprocess.run(['sh','execute_task.sh',task,param], check=False)
    except Exception as e:
        return jsonify({"status":"Error","message":str(e)}), 500
    return jsonify({"status":"Task execution started"})

@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    token = request.form.get('token')
    if token and hmac.compare_digest(token, SECRET_TOKEN):
        return jsonify({"status":"Verification successful"})
    return jsonify({"status":"Verification failed"}), 401

@app.route('/admin/update_token', methods=['POST'])
def admin_update_token():
    global SECRET_TOKEN
    current_token = request.form.get('current_token')
    new_token = request.form.get('new_token')
    if not current_token or not hmac.compare_digest(current_token, SECRET_TOKEN):
        return jsonify({"status":"Verification failed"}), 401
    if not new_token:
        return jsonify({"status":"Error","message":"Invalid new token"}), 400
    SECRET_TOKEN = new_token
    return jsonify({"status":"Token updated"})

@app.route('/config/retrieve', methods=['GET'])
def config_retrieve():
    config_name = request.args.get('config_name')
    if not config_name:
        return jsonify({"status":"Error","message":"Configuration name is required"}), 400
    return jsonify({"status":"Configuration retrieved","config":{"config_name":config_name,"config_value":"Example Config Value"}})

@app.route('/config/delete', methods=['POST'])
def config_delete():
    config_name = request.form.get('config_name')
    if not config_name:
        return jsonify({"status":"Error","message":"Configuration name is required"}), 400
    return jsonify({"status":"Configuration deleted","config_name":config_name})

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task status","task_id":task_id,"status":"Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    token = request.form.get('token')
    if not token or not hmac.compare_digest(token, SECRET_TOKEN):
        return jsonify({"status":"Access denied"}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting updated","setting":setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task logs","task_id":task_id,"logs":f"Logs for task {task_id}"})

@app.route('/backup/data', methods=['GET'])
def backup_data():
    backup_format = request.args.get('format', 'json').lower()
    if backup_format not in SAFE_FORMATS:
        return jsonify({"status":"Error","message":"Unsupported backup format"}), 400
    try:
        subprocess.run(['python3','backup_data.py',backup_format], check=False)
    except Exception as e:
        return jsonify({"status":"Error","message":str(e)}), 500
    return jsonify({"status":"Data backup started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User profile retrieved","profile":{"user_id":user_id,"name":"Michael Brown","email":"michael.brown@example.com"}})

if __name__ == '__main__':
    app.run(debug=False)