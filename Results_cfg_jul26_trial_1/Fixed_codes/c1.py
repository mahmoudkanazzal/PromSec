from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

SECRET_TOKEN = "secure_token_2024"

@app.route('/config/upload', methods=['POST'])
def upload_config():
    yaml_config = request.data.decode('utf-8')
    try:
        config = yaml.load(yaml_config, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    config_name = config.get('config_name', '')
    config_value = config.get('config_value', '')

    if not config_name or not config_value:
        return jsonify({"status": "Error", "message": "Missing configuration details"}), 400

    return jsonify({"status": "Configuration uploaded", "config_name": config_name, "config_value": config_value})

@app.route('/task/execute', methods=['GET'])
def execute_task():
    task = request.args.get('task', '')
    param = request.args.get('param', '')
    os.system(f"sh execute_task.sh {task} {param}")
    return jsonify({"status": "Task execution started"})

@app.route('/admin/verify', methods=['POST'])
def verify_admin():
    token = request.form.get('token', '')

    if token == SECRET_TOKEN:
        return jsonify({"status": "Verification successful"})
    else:
        return jsonify({"status": "Verification failed"}), 401

@app.route('/admin/update_token', methods=['POST'])
def update_token():
    current_token = request.form.get('current_token', '')

    if current_token != SECRET_TOKEN:
        return jsonify({"status": "Verification failed"}), 401
    
    new_token = request.form.get('new_token', '')
    if not new_token:
        return jsonify({"status": "Error", "message": "Invalid new token"}), 400

    global SECRET_TOKEN
    SECRET_TOKEN = new_token

    return jsonify({"status": "Token updated"})

@app.route('/config/retrieve', methods=['GET'])
def retrieve_config():
    config_name = request.args.get('config_name', '')
    if not config_name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400

    config = {
        "config_name": config_name,
        "config_value": "Example Config Value"
    }

    return jsonify({"status": "Configuration retrieved", "config": config})

@app.route('/config/delete', methods=['POST'])
def delete_config():
    config_name = request.form.get('config_name', '')
    if not config_name:
        return jsonify({"status": "Error", "message": "Configuration name is required"}), 400

    return jsonify({"status": "Configuration deleted", "config_name": config_name})

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    return jsonify({"status": "Task status", "task_id": task_id, "status": "Running"})

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    token = request.form.get('token', '')
    
    if token != SECRET_TOKEN:
        return jsonify({"status": "Access denied"}), 401
    
    setting = request.form.get('setting', '')
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400

    return jsonify({"status": "Setting updated", "setting": setting})

@app.route('/task/logs', methods=['GET'])
def get_task_logs():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    logs = "Logs for task " + task_id

    return jsonify({"status": "Task logs", "task_id": task_id, "logs": logs})

@app.route('/backup/data', methods=['GET'])
def backup_data():
    backup_format = request.args.get('format', 'json')
    os.system(f"python3 backup_data.py {backup_format}")
    return jsonify({"status": "Data backup started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    profile = {
        "user_id": user_id,
        "name": "Michael Brown",
        "email": "michael.brown@example.com"
    }

    return jsonify({"status": "User profile retrieved", "profile": profile})

app.run(debug=False)

