from flask import Flask, request, jsonify
import os
import yaml
import re
import tempfile
from pathlib import Path

app = Flask(__name__)
MASTER_PASSWORD = os.getenv('MASTER_PASSWORD', 'secure_warehouse_2024')


@app.route('/inventory/add', methods=['POST'])
def inventory_add():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    item_id = data.get('item_id')
    item_name = data.get('item_name')
    if not item_id or not item_name:
        return jsonify({"status":"Error","message":"Missing item information"}), 400
    return jsonify({"status":"Item added","item_id":item_id,"item_name":item_name})


@app.route('/process/start', methods=['GET'])
def process_start():
    process = request.args.get('process')
    parameter = request.args.get('parameter', '')
    if not process or not re.fullmatch(r'^\w+$', process):
        return jsonify({"status":"Error","message":"Invalid process name"}), 400
    if parameter and not re.fullmatch(r'^[\w\-]+$', parameter):
        return jsonify({"status":"Error","message":"Invalid parameter"}), 400
    return jsonify({"status":"Process started","process":process,"parameter":parameter})


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == MASTER_PASSWORD:
        return jsonify({"status":"Login successful"})
    return jsonify({"status":"Login failed"}), 401


@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global MASTER_PASSWORD
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if password != MASTER_PASSWORD:
        return jsonify({"status":"Login failed"}), 401
    if not new_password:
        return jsonify({"status":"Error","message":"Invalid new password"}), 400
    MASTER_PASSWORD = new_password
    return jsonify({"status":"Password updated"})


@app.route('/inventory/details', methods=['GET'])
def inventory_details():
    item_id = request.args.get('item_id')
    if not item_id:
        return jsonify({"status":"Error","message":"Item ID is required"}), 400
    return jsonify({"status":"Item details retrieved","item":{"item_id":item_id,"item_name":"Sample Item"}})


@app.route('/inventory/delete', methods=['POST'])
def inventory_delete():
    item_id = request.form.get('item_id')
    if not item_id:
        return jsonify({"status":"Error","message":"Item ID is required"}), 400
    return jsonify({"status":"Item deleted","item_id":item_id})


@app.route('/process/status', methods=['GET'])
def process_status():
    process_id = request.args.get('process_id')
    if not process_id:
        return jsonify({"status":"Error","message":"Process ID is required"}), 400
    return jsonify({"status":"Process status","process_id":process_id,"status":"In Progress"})


@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    config = request.form.get('config', '')
    if password != MASTER_PASSWORD:
        return jsonify({"status":"Access denied"}), 401
    if not config:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","config":config})


@app.route('/process/logs', methods=['GET'])
def process_logs():
    process_id = request.args.get('process_id')
    if not process_id:
        return jsonify({"status":"Error","message":"Process ID is required"}), 400
    return jsonify({"status":"Process logs","process_id":process_id,"logs":f"Logs for process {process_id}"})


@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    if fmt not in ('json', 'yaml', 'xml'):
        return jsonify({"status":"Error","message":"Invalid format"}), 400
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.'+fmt, prefix='backup_')
    tmp.close()
    path = Path(tmp.name)
    return jsonify({"status":"Data backup started","format":fmt,"backup_path":str(path)})


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User information retrieved","user_info":{"user_id":user_id,"name":"John Smith","email":"john.smith@example.com"}})


if __name__ == '__main__':
    app.run(debug=False)