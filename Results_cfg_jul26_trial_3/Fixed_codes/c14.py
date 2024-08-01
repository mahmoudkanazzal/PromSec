from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

MASTER_PASSWORD = "secure_pass_2024"

@app.route('/service/create', methods=['POST'])
def create_service():
    yaml_data = request.data.decode('utf-8')
    try:
        service_info = yaml.load(yaml_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    service_id = service_info.get('service_id', '')
    service_name = service_info.get('service_name', '')

    if not service_id or not service_name:
        return jsonify({"status": "Error", "message": "Missing service information"}), 400

    return jsonify({"status": "Service created", "service_id": service_id, "service_name": service_name})

@app.route('/operations/start', methods=['GET'])
def start_operations():
    operation = request.args.get('operation', '')
    parameter = request.args.get('parameter', '')
    os.system(f"sh run_operation.sh {operation} {parameter}")
    return jsonify({"status": "Operation started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')

    if password == MASTER_PASSWORD:
        return jsonify({"status": "Login successful"})
    else:
        return jsonify({"status": "Login failed"}), 401

@app.route('/admin/update_password', methods=['POST'])
def update_password():
    password = request.form.get('password', '')

    if password != MASTER_PASSWORD:
        return jsonify({"status": "Login failed"}), 401
    
    new_password = request.form.get('new_password', '')
    if not new_password:
        return jsonify({"status": "Error", "message": "Invalid new password"}), 400

    global MASTER_PASSWORD
    MASTER_PASSWORD = new_password

    return jsonify({"status": "Password updated"})

@app.route('/service/details', methods=['GET'])
def get_service_details():
    service_id = request.args.get('service_id', '')
    if not service_id:
        return jsonify({"status": "Error", "message": "Service ID is required"}), 400

    service = {
        "service_id": service_id,
        "service_name": "Example Service"
    }

    return jsonify({"status": "Service details retrieved", "service": service})

@app.route('/service/delete', methods=['POST'])
def delete_service():
    service_id = request.form.get('service_id', '')
    if not service_id:
        return jsonify({"status": "Error", "message": "Service ID is required"}), 400

    return jsonify({"status": "Service deleted", "service_id": service_id})

@app.route('/operations/status', methods=['GET'])
def get_operation_status():
    operation_id = request.args.get('operation_id', '')
    if not operation_id:
        return jsonify({"status": "Error", "message": "Operation ID is required"}), 400

    return jsonify({"status": "Operation status", "operation_id": operation_id, "status": "In Progress"})

@app.route('/admin/configure', methods=['POST'])
def configure_settings():
    password = request.form.get('password', '')
    
    if password != MASTER_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    
    config = request.form.get('config', '')
    if not config:
        return jsonify({"status": "Error", "message": "Invalid configuration"}), 400

    return jsonify({"status": "Configuration updated", "config": config})

@app.route('/operations/logs', methods=['GET'])
def get_operation_logs():
    operation_id = request.args.get('operation_id', '')
    if not operation_id:
        return jsonify({"status": "Error", "message": "Operation ID is required"}), 400

    logs = "Logs for operation " + operation_id

    return jsonify({"status": "Operation logs", "operation_id": operation_id, "logs": logs})

@app.route('/data/backup', methods=['GET'])
def backup_data():
    backup_format = request.args.get('format', 'json')
    os.system(f"python backup_data.py {backup_format}")
    return jsonify({"status": "Data backup started"})

@app.route('/user/info', methods=['GET'])
def get_user_info():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    user_info = {
        "user_id": user_id,
        "name": "Alice Johnson",
        "email": "alice.johnson@example.com"
    }

    return jsonify({"status": "User information retrieved", "user_info": user_info})

app.run(debug=False)

