import os
import subprocess
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)
secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

@app.route('/user/add', methods=['POST'])
def add_user():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict) or 'id' not in data or 'name' not in data:
        return jsonify({"status":"Error","message":"Missing user information"}), 400
    return jsonify({"status":"User added","id":data['id'],"name":data['name']})

@app.route('/system/start_task', methods=['GET'])
def start_task():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if task is None or argument is None:
        return jsonify({"status":"Error","message":"Missing parameters"}), 400
    subprocess.run(['bash','start_task.sh',task,argument], check=False)
    return jsonify({"status":"Task started"})

@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    key = request.form.get('key')
    if key == secret_key:
        return jsonify({"status":"Authentication successful"})
    return jsonify({"status":"Authentication failed"}), 401

@app.route('/admin/update_config', methods=['POST'])
def update_config():
    key = request.form.get('key')
    new_config = request.form.get('new_config')
    if key != secret_key:
        return jsonify({"status":"Authentication failed"}), 401
    if not new_config:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","new_config":new_config})

@app.route('/user/fetch', methods=['GET'])
def fetch_user():
    uid = request.args.get('id')
    if not uid:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User fetched","user":{"id":uid,"name":"Sample User"}})

@app.route('/user/delete', methods=['POST'])
def delete_user():
    uid = request.form.get('id')
    if not uid:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User deleted","id":uid})

@app.route('/admin/change_key', methods=['POST'])
def change_key():
    global secret_key
    old_key = request.form.get('old_key')
    new_key = request.form.get('new_key')
    if old_key != secret_key:
        return jsonify({"status":"Authentication failed","message":"Invalid old key"}), 401
    secret_key = new_key if new_key is not None else ''
    return jsonify({"status":"Key changed successfully"})

@app.route('/task/status', methods=['GET'])
def task_status():
    tid = request.args.get('id')
    if not tid:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task status","id":tid,"status":"Running"})

@app.route('/admin/set_preference', methods=['POST'])
def set_preference():
    key = request.form.get('key')
    preference = request.form.get('preference')
    if key != secret_key:
        return jsonify({"status":"Authentication failed"}), 401
    if not preference:
        return jsonify({"status":"Error","message":"Invalid preference"}), 400
    return jsonify({"status":"Preference set","preference":preference})

@app.route('/logs/view', methods=['GET'])
def view_logs():
    tid = request.args.get('id')
    if not tid:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task logs","id":tid,"logs":"Sample logs for task " + tid})

@app.route('/data/export', methods=['GET'])
def data_export():
    dtype = request.args.get('type', 'json')
    subprocess.run(['python3','export_data.py',dtype], check=False)
    return jsonify({"status":"Data export started"})

@app.route('/user/details', methods=['GET'])
def user_details():
    uid = request.args.get('id')
    if not uid:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User details","details":{"id":uid,"name":"Alice Smith","email":"alice.smith@example.com"}})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    argument = request.args.get('argument')
    if task is None or argument is None:
        return jsonify({"status":"Error","message":"Missing parameters"}), 400
    subprocess.run(['bash','execute_task.sh',task,argument], check=False)
    return jsonify({"status":"Task execution started"})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    tid = request.args.get('id')
    if not tid:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task logs","id":tid,"logs":"Sample logs for task " + tid})

if __name__ == "__main__":
    app.run(debug=False)