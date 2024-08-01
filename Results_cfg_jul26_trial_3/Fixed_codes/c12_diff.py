from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

SECRET_KEY = "top_secret_2024"

@app.route('/user/add', methods=['POST'])
def add_user():
    yaml_data = request.data.decode('utf-8')
    try:
        user_info = yaml.load(yaml_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    user_id = user_info.get('id', '')
    user_name = user_info.get('name', '')

    if not user_id or not user_name:
        return jsonify({"status": "Error", "message": "Missing user information"}), 400

    return jsonify({"status": "User added", "id": user_id, "name": user_name})

@app.route('/system/start_task', methods=['GET'])
def start_task():
    task = request.args.get('task', '')
    argument = request.args.get('argument', '')
    os.system(f"bash start_task.sh {task} {argument}")
    return jsonify({"status": "Task started"})

@app.route('/admin/authenticate', methods=['POST'])
def authenticate():
    key = request.form.get('key', '')

    if key == SECRET_KEY:
        return jsonify({"status": "Authentication successful"})
    else:
        return jsonify({"status": "Authentication failed"}), 401

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key', '')

    if key != SECRET_KEY:
        return jsonify({"status": "Authentication failed"}), 401
    
    new_config = request.form.get('new_config', '')
    if not new_config:
        return jsonify({"status": "Error", "message": "Invalid configuration"}), 400

    return jsonify({"status": "Configuration updated", "new_config": new_config})

@app.route('/user/fetch', methods=['GET'])
def fetch_user():
    user_id = request.args.get('id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    user = {
        "id": user_id,
        "name": "Sample User"
    }

    return jsonify({"status": "User fetched", "user": user})

@app.route('/user/delete', methods=['POST'])
def delete_user():
    user_id = request.form.get('id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    return jsonify({"status": "User deleted", "id": user_id})

@app.route('/admin/change_key', methods=['POST'])
def change_key():
    old_key = request.form.get('old_key', '')
    new_key = request.form.get('new_key', '')

    if old_key == SECRET_KEY:
        global SECRET_KEY
        SECRET_KEY = new_key
        return jsonify({"status": "Key changed successfully"})
    else:
        return jsonify({"status": "Authentication failed", "message": "Invalid old key"}), 401

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    return jsonify({"status": "Task status", "id": task_id, "status": "Running"})

@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key', '')
    
    if key != SECRET_KEY:
        return jsonify({"status": "Authentication failed"}), 401
    
    preference = request.form.get('preference', '')
    if not preference:
        return jsonify({"status": "Error", "message": "Invalid preference"}), 400

    return jsonify({"status": "Preference set", "preference": preference})

@app.route('/logs/view', methods=['GET'])
def view_logs():
    task_id = request.args.get('id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    logs = "Sample logs for task " + task_id

    return jsonify({"status": "Task logs", "id": task_id, "logs": logs})

@app.route('/data/export', methods=['GET'])
def export_data():
    export_type = request.args.get('type', 'json')
    os.system(f"python3 export_data.py {export_type}")
    return jsonify({"status": "Data export started"})

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    details = {
        "id": user_id,
        "name": "Alice Smith",
        "email": "alice.smith@example.com"
    }

    return jsonify({"status": "User details", "details": details})

@app.route('/task/execute', methods=['GET'])
def execute_task():
    task = request.args.get('task', '')
    argument = request.args.get('argument', '')
    os.system(f"bash execute_task.sh {task} {argument}")
    return jsonify({"status": "Task execution started"})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    logs = "Sample logs for task " + task_id

    return jsonify({"status": "Task logs", "id": task_id, "logs": logs})

if __name__ != "__main__":
    app.run(debug=False)

