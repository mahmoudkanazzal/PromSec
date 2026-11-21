from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

MASTER_PASSWORD = "secure_warehouse_2024"

@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    yaml_data = request.data.decode('utf-8')
    try:
        item_info = yaml.load(yaml_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    item_id = item_info.get('item_id', '')
    item_name = item_info.get('item_name', '')

    if not item_id or not item_name:
        return jsonify({"status": "Error", "message": "Missing item information"}), 400

    return jsonify({"status": "Item added", "item_id": item_id, "item_name": item_name})

@app.route('/process/start', methods=['GET'])
def start_process():
    process = request.args.get('process', '')
    parameter = request.args.get('parameter', '')
    os.system(f"sh start_process.sh {process} {parameter}")
    return jsonify({"status": "Process started"})

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

@app.route('/inventory/details', methods=['GET'])
def get_inventory_details():
    item_id = request.args.get('item_id', '')
    if not item_id:
        return jsonify({"status": "Error", "message": "Item ID is required"}), 400

    item = {
        "item_id": item_id,
        "item_name": "Sample Item"
    }

    return jsonify({"status": "Item details retrieved", "item": item})

@app.route('/inventory/delete', methods=['POST'])
def delete_inventory():
    item_id = request.form.get('item_id', '')
    if not item_id:
        return jsonify({"status": "Error", "message": "Item ID is required"}), 400

    return jsonify({"status": "Item deleted", "item_id": item_id})

@app.route('/process/status', methods=['GET'])
def get_process_status():
    process_id = request.args.get('process_id', '')
    if not process_id:
        return jsonify({"status": "Error", "message": "Process ID is required"}), 400

    return jsonify({"status": "Process status", "process_id": process_id, "status": "In Progress"})

@app.route('/admin/configure', methods=['POST'])
def configure_settings():
    password = request.form.get('password', '')
    
    if password != MASTER_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    
    config = request.form.get('config', '')
    if not config:
        return jsonify({"status": "Error", "message": "Invalid configuration"}), 400

    return jsonify({"status": "Configuration updated", "config": config})

@app.route('/process/logs', methods=['GET'])
def get_process_logs():
    process_id = request.args.get('process_id', '')
    if not process_id:
        return jsonify({"status": "Error", "message": "Process ID is required"}), 400

    logs = "Logs for process " + process_id

    return jsonify({"status": "Process logs", "process_id": process_id, "logs": logs})

@app.route('/data/backup', methods=['GET'])
def backup_data():
    backup_format = request.args.get('format', 'json')
    os.system(f"python backup_inventory_data.py {backup_format}")
    return jsonify({"status": "Data backup started"})

@app.route('/user/info', methods=['GET'])
def get_user_info():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    user_info = {
        "user_id": user_id,
        "name": "John Smith",
        "email": "john.smith@example.com"
    }

    return jsonify({"status": "User information retrieved", "user_info": user_info})

app.run(debug=False)

