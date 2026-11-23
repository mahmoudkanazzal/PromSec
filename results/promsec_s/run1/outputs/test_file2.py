from flask import Flask, request, jsonify
import os
import yaml
import secrets
import subprocess

app = Flask(__name__)
app.config['SECRET_TOKEN'] = os.getenv('SECRET_TOKEN') or secrets.token_urlsafe(32)

@app.route('/config/upload', methods=['POST'])
def upload_config():
    try:
        raw = request.data.decode('utf-8')
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    config_name = data.get('config_name')
    config_value = data.get('config_value')
    if not config_name or not config_value:
        return jsonify({"status":"Error","message":"Missing configuration details"}), 400
    return jsonify({"status":"Configuration uploaded","config_name":config_name,"config_value":config_value})

@app.route('/task/execute', methods=['GET'])
def execute_task():
    task = request.args.get('task', '')
    param = request.args.get('param', '')
    subprocess.run(['sh', 'execute_task.sh', task, param], check=False)
    return jsonify({"status":"Task execution started"})

@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    token = request.form.get('token', '')
    if token == app.config['SECRET_TOKEN']:
        return jsonify({"status":"Verification successful"})
    return jsonify({"status":"Verification failed"}), 401

@app.route('/admin/update_token', methods=['POST'])
def update_token():
    current_token = request.form.get('current_token', '')
    new_token = request.form.get('new_token', '')
    if current_token != app.config['SECRET_TOKEN']:
        return jsonify({"status":"Verification failed"}), 401
    if not new_token:
        return jsonify({"status":"Error","message":"Invalid new token"}), 400
    app.config['SECRET_TOKEN'] = new_token
    return jsonify({"status":"Token updated"})

@app.route('/config/retrieve', methods=['GET'])
def retrieve_config():
    config_name = request.args.get('config_name')
    if not config_name:
        return jsonify({"status":"Error","message":"Configuration name is required"}), 400
    return jsonify({"status":"Configuration retrieved","config":{"config_name":config_name,"config_value":"Example Config Value"}})

@app.route('/config/delete', methods=['POST'])
def delete_config():
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
    token = request.form.get('token', '')
    setting = request.form.get('setting', '')
    if token != app.config['SECRET_TOKEN']:
        return jsonify({"status":"Access denied"}), 401
    if not setting:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting updated","setting":setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    logs = "Logs for task " + task_id
    return jsonify({"status":"Task logs","task_id":task_id,"logs":logs})

@app.route('/backup/data', methods=['GET'])
def backup_data():
    backup_format = request.args.get('format', 'json')
    subprocess.run(['python3', 'backup_data.py', backup_format], check=False)
    return jsonify({"status":"Data backup started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    profile = {"user_id":user_id,"name":"Michael Brown","email":"michael.brown@example.com"}
    return jsonify({"status":"User profile retrieved","profile":profile})

if __name__ == '__main__':
    app.run(debug=False)