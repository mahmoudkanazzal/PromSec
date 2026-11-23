from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

MASTER_PASSWORD_PLAIN = os.getenv('MASTER_PASSWORD_PLAIN', 'secure_warehouse_2024')
MASTER_PASSWORD_HASH = generate_password_hash(MASTER_PASSWORD_PLAIN)

SAFE_NAME_RE = re.compile(r'^[\w\-]+$')


def error_response(message, status_code):
    return jsonify({'error': message}), status_code


@app.route('/inventory/add', methods=['POST'])
def inventory_add():
    raw_body = request.get_data(as_text=True)
    if not raw_body:
        return error_response('Empty request body', 400)
    try:
        data = yaml.safe_load(raw_body)
    except yaml.YAMLError:
        return error_response('Invalid YAML', 400)
    if not isinstance(data, dict):
        return error_response('YAML must be a mapping', 400)
    item_id = data.get('item_id')
    item_name = data.get('item_name')
    if not item_id or not item_name:
        return error_response('Missing item_id or item_name', 400)
    return jsonify({'status': 'success', 'item_id': item_id, 'item_name': item_name})


@app.route('/process/start', methods=['GET'])
def process_start():
    process = request.args.get('process')
    parameter = request.args.get('parameter')
    if not process or not parameter:
        return error_response('Missing process or parameter', 400)
    if not SAFE_NAME_RE.match(process) or not SAFE_NAME_RE.match(parameter):
        return error_response('Invalid characters in process or parameter', 400)
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'start_process.sh'))
    try:
        subprocess.run(['sh', script_path, process, parameter],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return error_response('Failed to start process', 500)
    return jsonify({'status': 'process started'})


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if not password:
        return error_response('Password required', 400)
    if check_password_hash(MASTER_PASSWORD_HASH, password):
        return jsonify({'status': 'login successful'})
    return error_response('Invalid credentials', 401)


@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global MASTER_PASSWORD_HASH
    password = request.form.get('password')
    new_password = request.form.get('new_password')
    if not password:
        return error_response('Current password required', 400)
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        return error_response('Invalid current password', 401)
    if not new_password:
        return error_response('New password cannot be empty', 400)
    MASTER_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'status': 'password updated'})


@app.route('/inventory/details', methods=['GET'])
def inventory_details():
    item_id = request.args.get('item_id')
    if not item_id:
        return error_response('item_id required', 400)
    return jsonify({'item_id': item_id, 'item_name': 'Sample Item'})


@app.route('/inventory/delete', methods=['POST'])
def inventory_delete():
    item_id = request.form.get('item_id')
    if not item_id:
        return error_response('item_id required', 400)
    return jsonify({'status': f'Item {item_id} deleted'})


@app.route('/process/status', methods=['GET'])
def process_status():
    process_id = request.args.get('process_id')
    if not process_id:
        return error_response('process_id required', 400)
    return jsonify({'process_id': process_id, 'status': 'In Progress'})


@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    config = request.form.get('config')
    if not password:
        return error_response('Password required', 400)
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        return error_response('Invalid credentials', 401)
    if not config:
        return error_response('Config cannot be empty', 400)
    return jsonify({'status': 'configuration applied', 'config': config})


@app.route('/process/logs', methods=['GET'])
def process_logs():
    process_id = request.args.get('process_id')
    if not process_id:
        return error_response('process_id required', 400)
    return jsonify({'process_id': process_id, 'logs': f'Logs for process {process_id}'})


@app.route('/data/backup', methods=['GET'])
def data_backup():
    backup_format = request.args.get('format', 'json')
    if backup_format not in ('json', 'yaml', 'csv'):
        return error_response('Invalid format', 400)
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup_inventory_data.py'))
    try:
        subprocess.run(['python', script_path, backup_format],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return error_response('Backup failed', 500)
    return jsonify({'status': f'Backup completed in {backup_format} format'})


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return error_response('user_id required', 400)
    return jsonify({
        'user_id': user_id,
        'name': 'John Smith',
        'email': 'john.smith@example.com'
    })


if __name__ == '__main__':
    app.run(debug=False)