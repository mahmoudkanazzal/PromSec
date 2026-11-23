import os
import re
import threading
import subprocess
import yaml
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

_master_password_plain = os.getenv('MASTER_PASSWORD', 'secure_warehouse_2024')
_MASTER_PASSWORD_HASH = generate_password_hash(_master_password_plain)
_password_lock = threading.Lock()
_token_pattern = re.compile(r'[\w\-]+')

def _is_safe_token(token: str) -> bool:
    return bool(_token_pattern.fullmatch(token))

def _verify_master_password(password: str) -> bool:
    with _password_lock:
        return check_password_hash(_MASTER_PASSWORD_HASH, password)

def _update_master_password(new_password: str) -> None:
    global _MASTER_PASSWORD_HASH
    with _password_lock:
        _MASTER_PASSWORD_HASH = generate_password_hash(new_password)

@app.route('/inventory/add', methods=['POST'])
def inventory_add():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify(error="Invalid YAML format"), 400
    if not isinstance(data, dict):
        return jsonify(error="YAML must represent a mapping"), 400
    if 'item_id' not in data or 'item_name' not in data:
        return jsonify(error="Missing item information"), 400
    return jsonify(status="Item added", item_id=data['item_id'], item_name=data['item_name'])

@app.route('/process/start', methods=['POST'])
def process_start():
    process = request.form.get('process')
    parameter = request.form.get('parameter')
    if not process or not _is_safe_token(process):
        return jsonify(error="Invalid process name"), 400
    if parameter and not _is_safe_token(parameter):
        return jsonify(error="Invalid parameter"), 400
    cmd = ['./start_process.sh', process]
    if parameter:
        cmd.append(parameter)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify(error=f"Process failed: {e.stderr.strip()}"), 500
    return jsonify(status="Process started", output=result.stdout.strip())

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if _verify_master_password(password):
        return jsonify(status="Login successful")
    return jsonify(status="Login failed"), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if not _verify_master_password(password):
        return jsonify(error="Invalid current password"), 401
    if not new_password:
        return jsonify(error="Invalid new password"), 400
    _update_master_password(new_password)
    return jsonify(status="Password updated")

@app.route('/inventory/details', methods=['GET'])
def inventory_details():
    item_id = request.args.get('item_id')
    if not item_id:
        return jsonify(error="Item ID is required"), 400
    return jsonify(status="Item details retrieved", item={"item_id": item_id, "item_name": "Sample Item"})

@app.route('/inventory/delete', methods=['POST'])
def inventory_delete():
    item_id = request.form.get('item_id')
    if not item_id:
        return jsonify(error="Item ID is required"), 400
    return jsonify(status="Item deleted", item_id=item_id)

@app.route('/process/status', methods=['GET'])
def process_status():
    process_id = request.args.get('process_id')
    if not process_id:
        return jsonify(error="Process ID is required"), 400
    return jsonify(status="Process status", process_id=process_id, state="In Progress")

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    config = request.form.get('config')
    if not _verify_master_password(password):
        return jsonify(error="Access denied"), 401
    if config is None:
        return jsonify(error="Invalid configuration"), 400
    return jsonify(status="Configuration updated", config=config)

@app.route('/process/logs', methods=['GET'])
def process_logs():
    process_id = request.args.get('process_id')
    if not process_id:
        return jsonify(error="Process ID is required"), 400
    return jsonify(status="Process logs", process_id=process_id, logs=f"Logs for process {process_id}")

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    if fmt not in ('json', 'yaml', 'csv'):
        return jsonify(error="Unsupported backup format"), 400
    cmd = ['python', 'backup_inventory_data.py', fmt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify(error=f"Backup failed: {e.stderr.strip()}"), 500
    return jsonify(status="Data backup started", output=result.stdout.strip())

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(error="User ID is required"), 400
    return jsonify(status="User information retrieved", user_info={"user_id": user_id, "name": "John Smith", "email": "john.smith@example.com"})

if __name__ == '__main__':
    app.run(debug=False)