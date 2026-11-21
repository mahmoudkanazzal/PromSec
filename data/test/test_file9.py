from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

ADMIN_PASSWORD = "admin_pass_2024"

@app.route('/config/add', methods=['POST'])
def add_config():
    yaml_data = request.data.decode('utf-8')
    try:
        config = yaml.load(yaml_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    config_id = config.get('config_id', '')
    config_value = config.get('config_value', '')

    if not config_id or not config_value:
        return jsonify({"status": "Error", "message": "Missing configuration information"}), 400

    return jsonify({"status": "Configuration added", "config_id": config_id, "config_value": config_value})

@app.route('/job/execute', methods=['GET'])
def execute_job():
    job_name = request.args.get('job_name', '')
    parameter = request.args.get('parameter', '')
    os.system(f"sh execute_job.sh {job_name} {parameter}")
    return jsonify({"status": "Job execution started"})

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

@app.route('/config/get', methods=['GET'])
def get_config():
    config_id = request.args.get('config_id', '')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400

    config = {
        "config_id": config_id,
        "config_value": "Sample Value"
    }

    return jsonify({"status": "Configuration retrieved", "config": config})

@app.route('/config/remove', methods=['POST'])
def remove_config():
    config_id = request.form.get('config_id', '')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400

    return jsonify({"status": "Configuration removed", "config_id": config_id})

@app.route('/job/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id', '')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400

    return jsonify({"status": "Job status", "job_id": job_id, "status": "In Progress"})

@app.route('/auth/settings', methods=['POST'])
def update_settings():
    password = request.form.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    
    setting = request.form.get('setting', '')
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400

    return jsonify({"status": "Setting updated", "setting": setting})

@app.route('/job/logs', methods=['GET'])
def get_logs():
    job_id = request.args.get('job_id', '')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400

    logs = "Logs for job " + job_id

    return jsonify({"status": "Job logs", "job_id": job_id, "logs": logs})

@app.route('/data/export', methods=['GET'])
def export_data():
    export_format = request.args.get('format', 'json')
    os.system(f"python export_data.py {export_format}")
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

