from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

ADMIN_PASSWORD = "event_admin_2024"

@app.route('/event/add', methods=['POST'])
def add_event():
    yaml_data = request.data.decode('utf-8')
    try:
        event = yaml.load(yaml_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    event_id = event.get('event_id', '')
    event_name = event.get('event_name', '')
    event_date = event.get('event_date', '')

    if not event_id or not event_name or not event_date:
        return jsonify({"status": "Error", "message": "Missing event information"}), 400

    return jsonify({"status": "Event added", "event_id": event_id, "event_name": event_name, "event_date": event_date})

@app.route('/event/start', methods=['GET'])
def start_event():
    event_id = request.args.get('event_id', '')
    task = request.args.get('task', '')
    os.system(f"sh start_event.sh {event_id} {task}")
    return jsonify({"status": "Event started"})

@app.route('/auth/login', methods=['POST'])
def login():
    password = request.form.get('password', '')

    if password == ADMIN_PASSWORD:
        return jsonify({"status": "Login successful"})
    else:
        return jsonify({"status": "Login failed"}), 401

@app.route('/auth/update_password', methods=['POST'])
def update_password():
    password = request.form.get('password', '')

    if password != ADMIN_PASSWORD:
        return jsonify({"status": "Login failed"}), 401
    
    new_password = request.form.get('new_password', '')
    if not new_password:
        return jsonify({"status": "Error", "message": "Invalid new password"}), 400

    global ADMIN_PASSWORD
    ADMIN_PASSWORD = new_password

    return jsonify({"status": "Password updated"})

@app.route('/event/get', methods=['GET'])
def get_event():
    event_id = request.args.get('event_id', '')
    if not event_id:
        return jsonify({"status": "Error", "message": "Event ID is required"}), 400

    event = {
        "event_id": event_id,
        "event_name": "Sample Event",
        "event_date": "2024-01-01"
    }

    return jsonify({"status": "Event retrieved", "event": event})

@app.route('/event/remove', methods=['POST'])
def remove_event():
    event_id = request.form.get('event_id', '')
    if not event_id:
        return jsonify({"status": "Error", "message": "Event ID is required"}), 400

    return jsonify({"status": "Event removed", "event_id": event_id})

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    return jsonify({"status": "Task status", "task_id": task_id, "status": "In Progress"})

@app.route('/auth/settings', methods=['POST'])
def update_settings():
    password = request.form.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    
    setting = request.form.get('setting', '')
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400

    return jsonify({"status": "Setting updated", "setting": setting})

@app.route('/task/logs', methods=['GET'])
def get_logs():
    task_id = request.args.get('task_id', '')
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400

    logs = "Logs for task " + task_id

    return jsonify({"status": "Task logs", "task_id": task_id, "logs": logs})

@app.route('/data/export', methods=['GET'])
def export_data():
    export_format = request.args.get('format', 'json')
    os.system(f"python export_event_data.py {export_format}")
    return jsonify({"status": "Data export started"})

@app.route('/user/info', methods=['GET'])
def get_user_info():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    user_info = {
        "user_id": user_id,
        "name": "John Doe",
        "email": "john.doe@example.com"
    }

    return jsonify({"status": "User information retrieved", "user_info": user_info})

if __name__ != "__main__":
    app.run(debug=False)

