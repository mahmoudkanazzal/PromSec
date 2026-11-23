import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'default_insecure_key')
app.secret_key = SECRET_KEY

def _is_safe_token(token: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', token))

@app.route('/system/add_record', methods=['POST'])
def add_record():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"YAML must represent a mapping"}), 400
    rec_id = data.get('id')
    value = data.get('value')
    if not rec_id or not value:
        return jsonify({"status":"Error","message":"Missing record information"}), 400
    return jsonify({"status":"Record added","id":rec_id,"value":value}), 200

@app.route('/system/start_process', methods=['GET'])
def start_process():
    process = request.args.get('process')
    argument = request.args.get('argument')
    if not process or not _is_safe_token(process):
        return jsonify({"status":"Error","message":"Invalid process token"}), 400
    if not argument or not _is_safe_token(argument):
        return jsonify({"status":"Error","message":"Invalid argument token"}), 400
    subprocess.run(["bash","start_process.sh",process,argument], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return jsonify({"status":"Process started"}), 200

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key', '')
    if key == SECRET_KEY:
        return jsonify({"status":"Authentication successful"}), 200
    return jsonify({"status":"Authentication failed"}), 401

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key', '')
    if key != SECRET_KEY:
        return jsonify({"status":"Authentication failed"}), 401
    new_config = request.form.get('new_config', '')
    if not new_config:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","new_config":new_config}), 200

@app.route('/records/fetch', methods=['GET'])
def fetch_record():
    rec_id = request.args.get('id')
    if not rec_id:
        return jsonify({"status":"Error","message":"Record ID is required"}), 400
    return jsonify({"status":"Record fetched","record":{"id":rec_id,"value":"Sample Value"}}), 200

@app.route('/records/delete', methods=['POST'])
def delete_record():
    rec_id = request.form.get('id')
    if not rec_id:
        return jsonify({"status":"Error","message":"Record ID is required"}), 400
    return jsonify({"status":"Record deleted","id":rec_id}), 200

@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global SECRET_KEY
    old_key = request.form.get('old_key', '')
    new_key = request.form.get('new_key', '')
    if old_key != SECRET_KEY:
        return jsonify({"status":"Authentication failed","message":"Invalid old key"}), 401
    if not new_key:
        return jsonify({"status":"Error","message":"New key cannot be empty"}), 400
    SECRET_KEY = new_key
    app.secret_key = new_key
    return jsonify({"status":"Key changed successfully"}), 200

@app.route('/process/status', methods=['GET'])
def process_status():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify({"status":"Error","message":"Process ID is required"}), 400
    return jsonify({"status":"Process status","id":proc_id,"status":"Running"}), 200

@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key', '')
    if key != SECRET_KEY:
        return jsonify({"status":"Authentication failed"}), 401
    preference = request.form.get('preference', '')
    if not preference:
        return jsonify({"status":"Error","message":"Invalid preference"}), 400
    return jsonify({"status":"Preference set","preference":preference}), 200

@app.route('/logs/view', methods=['GET'])
def view_logs():
    proc_id = request.args.get('id')
    if not proc_id:
        return jsonify({"status":"Error","message":"Process ID is required"}), 400
    return jsonify({"status":"Process logs","id":proc_id,"logs":f"Sample logs for process {proc_id}"}), 200

@app.route('/data/export', methods=['GET'])
def data_export():
    export_type = request.args.get('type', 'json')
    if not _is_safe_token(export_type):
        return jsonify({"status":"Error","message":"Invalid export type"}), 400
    subprocess.run(["python3","export_data.py",export_type], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return jsonify({"status":"Data export started"}), 200

@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User details","details":{"id":user_id,"name":"Alice Smith","email":"alice.smith@example.com"}}), 200

if __name__ == "__main__":
    app.run(debug=False)