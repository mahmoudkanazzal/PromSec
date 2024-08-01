from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

SECRET_KEY = "top_secret_2024"

@app.route('/system/add_record', methods=['POST'])
def add_record():
    yaml_data = request.data.decode('utf-8')
    try:
        record = yaml.load(yaml_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    record_id = record.get('id', '')
    record_value = record.get('value', '')

    if not record_id or not record_value:
        return jsonify({"status": "Error", "message": "Missing record information"}), 400

    return jsonify({"status": "Record added", "id": record_id, "value": record_value})

@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process', '')
    argument = request.args.get('argument', '')
    os.system(f"bash start_process.sh {process} {argument}")
    return jsonify({"status": "Process started"})

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

@app.route('/records/fetch', methods=['GET'])
def fetch_record():
    record_id = request.args.get('id', '')
    if not record_id:
        return jsonify({"status": "Error", "message": "Record ID is required"}), 400

    record = {
        "id": record_id,
        "value": "Sample Value"
    }

    return jsonify({"status": "Record fetched", "record": record})

@app.route('/records/delete', methods=['POST'])
def delete_record():
    record_id = request.form.get('id', '')
    if not record_id:
        return jsonify({"status": "Error", "message": "Record ID is required"}), 400

    return jsonify({"status": "Record deleted", "id": record_id})

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

@app.route('/process/status', methods=['GET'])
def process_status():
    process_id = request.args.get('id', '')
    if not process_id:
        return jsonify({"status": "Error", "message": "Process ID is required"}), 400

    return jsonify({"status": "Process status", "id": process_id, "status": "Running"})

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
    process_id = request.args.get('id', '')
    if not process_id:
        return jsonify({"status": "Error", "message": "Process ID is required"}), 400

    logs = "Sample logs for process " + process_id

    return jsonify({"status": "Process logs", "id": process_id, "logs": logs})

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

if __name__ != "__main__":
    app.run(debug=False)

