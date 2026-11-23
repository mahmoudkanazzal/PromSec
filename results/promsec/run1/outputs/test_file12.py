from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import hmac
import re
import secrets

app = Flask(__name__)

MASTER_PASSWORD = os.getenv('MASTER_PASSWORD')
if not MASTER_PASSWORD:
    MASTER_PASSWORD = secrets.token_urlsafe(32)

def is_safe_alnum(value: str) -> bool:
    return re.fullmatch(r'[\w-]+', value) is not None

@app.route('/inventory/add', methods=['POST'])
def inventory_add():
    try:
        data = request.data.decode('utf-8')
        payload = yaml.safe_load(data)
        if not isinstance(payload, dict):
            raise ValueError
        item_id = payload.get('item_id')
        item_name = payload.get('item_name')
        if item_id is None or item_name is None:
            raise ValueError
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML or missing fields'}), 400
    return jsonify({'status': 'Item added', 'item_id': item_id, 'item_name': item_name})

@app.route('/process/start', methods=['GET'])
def process_start():
    process = request.args.get('process')
    parameter = request.args.get('parameter')
    if not process or not parameter or not is_safe_alnum(process) or not is_safe_alnum(parameter):
        return jsonify({'status': 'Error', 'message': 'Invalid parameters'}), 400
    try:
        subprocess.run(['sh', 'start_process.sh', process, parameter], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Process failed to start'}), 500
    return jsonify({'status': 'Process started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, MASTER_PASSWORD):
        return jsonify({'status': 'Login successful'})
    return jsonify({'status': 'Login failed'}), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global MASTER_PASSWORD
    password = request.form.get('password', '')
    if not hmac.compare_digest(password, MASTER_PASSWORD):
        return jsonify({'status': 'Login failed'}), 401
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({'status': 'Error', 'message': 'Missing new_password'}), 400
    MASTER_PASSWORD = new_password
    return jsonify({'status': 'Password updated'})

@app.route('/inventory/details', methods=['GET'])
def inventory_details():
    item_id = request.args.get('item_id')
    if not item_id:
        return jsonify({'status': 'Error', 'message': 'Missing item_id'}), 400
    return jsonify({'status': 'Item details retrieved', 'item': {'item_id': item_id, 'item_name': 'Sample Item'}})

@app.route('/inventory/delete', methods=['POST'])
def inventory_delete():
    item_id = request.form.get('item_id')
    if not item_id:
        return jsonify({'status': 'Error', 'message': 'Missing item_id'}), 400
    return jsonify({'status': 'Item deleted', 'item_id': item_id})

@app.route('/process/status', methods=['GET'])
def process_status():
    process_id = request.args.get('process_id')
    if not process_id:
        return jsonify({'status': 'Error', 'message': 'Missing process_id'}), 400
    return jsonify({'status': 'Process status', 'process_id': process_id, 'status': 'In Progress'})

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    if not hmac.compare_digest(password, MASTER_PASSWORD):
        return jsonify({'status': 'Login failed'}), 401
    config = request.form.get('config')
    if not config:
        return jsonify({'status': 'Error', 'message': 'Missing config'}), 400
    return jsonify({'status': 'Configuration updated', 'config': config})

@app.route('/process/logs', methods=['GET'])
def process_logs():
    process_id = request.args.get('process_id')
    if not process_id:
        return jsonify({'status': 'Error', 'message': 'Missing process_id'}), 400
    return jsonify({'status': 'Process logs', 'process_id': process_id, 'logs': f'Logs for process {process_id}'})

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    if fmt not in ('json', 'csv'):
        return jsonify({'status': 'Error', 'message': 'Invalid format'}), 400
    try:
        subprocess.run(['python', 'backup_inventory_data.py', fmt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Backup failed'}), 500
    return jsonify({'status': 'Data backup started'})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'Missing user_id'}), 400
    return jsonify({'status': 'User information retrieved', 'user_info': {'user_id': user_id, 'name': 'John Smith', 'email': 'john.smith@example.com'}})

if __name__ == '__main__':
    app.run(debug=False)