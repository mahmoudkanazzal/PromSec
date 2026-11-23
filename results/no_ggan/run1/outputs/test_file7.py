import os
import secrets
import hmac
import subprocess
import re
from flask import Flask, request, jsonify

def constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1, val2)

def _is_safe_argument(arg: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z0-9._-]+', arg))

app = Flask(__name__)

secret_key = os.getenv('APP_SECRET_KEY')
if not secret_key:
    secret_key = secrets.token_urlsafe(32)
    os.environ['APP_SECRET_KEY'] = secret_key
app.config['SECRET_KEY'] = secret_key
SECRET_KEY = secret_key

@app.route('/system/add_record', methods=['POST'])
def add_record():
    raw = request.get_data(as_text=True)
    try:
        data = __import__('yaml').safe_load(raw)
    except Exception:
        return jsonify(message="Invalid YAML format"), 400
    if not isinstance(data, dict):
        return jsonify(message="YAML must represent a mapping"), 400
    rec_id = data.get('id')
    value = data.get('value')
    if not rec_id or not value:
        return jsonify(message="Missing record information"), 400
    return jsonify(status="Record added", id=rec_id, value=value)

@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process')
    argument = request.args.get('argument')
    if not process or not _is_safe_argument(process):
        return jsonify(message="Invalid process name"), 400
    if not argument or not _is_safe_argument(argument):
        return jsonify(message="Invalid argument"), 400
    try:
        subprocess.run(
            ["bash", "start_process.sh", process, argument],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return jsonify(message="Failed to start process"), 500
    return jsonify(status="Process started")

def authenticate_key(key: str):
    return constant_time_compare(key or "", SECRET_KEY)

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key', '')
    if authenticate_key(key):
        return jsonify(status="Authentication successful")
    return jsonify(status="Authentication failed"), 401

@app.route('/admin/update_config', methods=['POST'])
def admin_update_config():
    key = request.form.get('key', '')
    if not authenticate_key(key):
        return jsonify(status="Authentication failed"), 401
    new_config = request.form.get('new_config')
    if not new_config:
        return jsonify(message="Invalid configuration"), 400
    return jsonify(status="Configuration updated", new_config=new_config)

@app.route('/records/fetch', methods=['GET'])
def records_fetch():
    rec_id = request.args.get('id')
    if not rec_id:
        return jsonify(message="Record ID is required"), 400
    record = {"id": rec_id, "value": "Sample Value"}
    return jsonify(status="Record fetched", record=record)

@app.route('/records/delete', methods=['POST'])
def records_delete():
    rec_id = request.form.get('id')
    if not rec_id:
        return jsonify(message="Record ID is required"), 400
    return jsonify(status="Record deleted", id=rec_id)

@app.route('/admin/change_key', methods=['POST'])
def admin_change_key():
    old_key = request.form.get('old_key', '')
    new_key = request.form.get('new_key', '')
    if not authenticate_key(old_key):
        return jsonify(status="Authentication failed", error="Invalid old key"), 401
    if not new_key:
        return jsonify(message="New key must not be empty"), 400
    global SECRET_KEY
    SECRET_KEY = new_key
    os.environ['APP_SECRET_KEY'] = new_key
    app.config['SECRET_KEY'] = new_key
    return jsonify(status="Key changed successfully")

@app.route('/process/status', methods=['GET'])
def process_status():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify(message="Process ID is required"), 400
    return jsonify(status="Process status", id=proc_id, status_detail="Running")

@app.route('/admin/set_preference', methods=['POST'])
def admin_set_preference():
    key = request.form.get('key', '')
    if not authenticate_key(key):
        return jsonify(status="Authentication failed"), 401
    pref = request.form.get('preference')
    if not pref:
        return jsonify(message="Invalid preference"), 400
    return jsonify(status="Preference set", preference=pref)

@app.route('/logs/view', methods=['GET'])
def logs_view():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify(message="Process ID is required"), 400
    return jsonify(status="Process logs", id=proc_id, logs=f"Sample logs for process {proc_id}")

@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    if export_type not in ('json', 'csv'):
        return jsonify(message=f"Unsupported export type: {export_type}"), 400
    try:
        subprocess.run(
            ["python3", "export_data.py", export_type],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return jsonify(message="Data export failed"), 500
    return jsonify(status="Data export started")

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify(message="User ID is required"), 400
    details = {"id": user_id, "name": "Alice Smith", "email": "alice.smith@example.com"}
    return jsonify(status="User details", details=details)

if __name__ == '__main__':
    app.run(debug=False)