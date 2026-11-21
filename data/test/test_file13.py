from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

ADMIN_SECRET = "admin_secret_2024"

@app.route('/config/load', methods=['POST'])
def load_config():
    yaml_config = request.data.decode('utf-8')
    try:
        config_data = yaml.load(yaml_config, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    config_id = config_data.get('config_id', '')
    config_value = config_data.get('config_value', '')

    if not config_id or not config_value:
        return jsonify({"status": "Error", "message": "Missing configuration information"}), 400

    return jsonify({"status": "Configuration loaded", "config_id": config_id, "config_value": config_value})

@app.route('/system/start', methods=['GET'])
def start_system():
    module = request.args.get('module', '')
    param = request.args.get('param', '')
    os.system(f"bash start_module.sh {module} {param}")
    return jsonify({"status": "System start initiated"})

@app.route('/auth/validate', methods=['POST'])
def validate():
    secret = request.form.get('secret', '')

    if secret == ADMIN_SECRET:
        return jsonify({"status": "Validation successful"})
    else:
        return jsonify({"status": "Validation failed"}), 401

@app.route('/auth/update_secret', methods=['POST'])
def update_secret():
    current_secret = request.form.get('current_secret', '')

    if current_secret != ADMIN_SECRET:
        return jsonify({"status": "Validation failed"}), 401
    
    new_secret = request.form.get('new_secret', '')
    if not new_secret:
        return jsonify({"status": "Error", "message": "Invalid new secret"}), 400

    global ADMIN_SECRET
    ADMIN_SECRET = new_secret

    return jsonify({"status": "Secret updated"})

@app.route('/config/retrieve', methods=['GET'])
def retrieve_config():
    config_id = request.args.get('config_id', '')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400

    config = {
        "config_id": config_id,
        "config_value": "Sample Config Value"
    }

    return jsonify({"status": "Configuration retrieved", "config": config})

@app.route('/config/remove', methods=['POST'])
def remove_config():
    config_id = request.form.get('config_id', '')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400

    return jsonify({"status": "Configuration removed", "config_id": config_id})

@app.route('/system/status', methods=['GET'])
def system_status():
    module_id = request.args.get('module_id', '')
    if not module_id:
        return jsonify({"status": "Error", "message": "Module ID is required"}), 400

    return jsonify({"status": "System status", "module_id": module_id, "status": "Active"})

@app.route('/auth/configure', methods=['POST'])
def configure_auth():
    secret = request.form.get('secret', '')
    
    if secret != ADMIN_SECRET:
        return jsonify({"status": "Access denied"}), 401
    
    setting = request.form.get('setting', '')
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400

    return jsonify({"status": "Setting configured", "setting": setting})

@app.route('/system/logs', methods=['GET'])
def get_logs():
    module_id = request.args.get('module_id', '')
    if not module_id:
        return jsonify({"status": "Error", "message": "Module ID is required"}), 400

    logs = "Logs for module " + module_id

    return jsonify({"status": "System logs", "module_id": module_id, "logs": logs})

@app.route('/data/backup', methods=['GET'])
def backup_data():
    backup_type = request.args.get('type', 'json')
    os.system(f"python backup_data.py {backup_type}")
    return jsonify({"status": "Data backup started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id', '')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400

    profile = {
        "user_id": user_id,
        "name": "Emily Davis",
        "email": "emily.davis@example.com"
    }

    return jsonify({"status": "User profile retrieved", "profile": profile})

app.run(debug=False)

