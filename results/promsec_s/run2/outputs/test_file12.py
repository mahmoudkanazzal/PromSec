from flask import Flask, request, jsonify
import os
import subprocess
from yaml import safe_load

app = Flask(__name__)
MASTER_PASSWORD = os.getenv('MASTER_PASSWORD', '')

@app.route('/inventory/add', methods=['POST'])
def inventory_add():
    try:
        raw = request.data.decode('utf-8')
        data = safe_load(raw)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='YAML must define a mapping'), 400
    item_id = data.get('item_id')
    item_name = data.get('item_name')
    if not item_id or not item_name:
        return jsonify(error='Missing item_id or item_name'), 400
    return jsonify(status='Item added', item_id=item_id, item_name=item_name)

@app.route('/process/start', methods=['GET'])
def process_start():
    proc = request.args.get('process')
    param = request.args.get('parameter')
    if not proc or not param:
        return jsonify(error='Missing process or parameter'), 400
    subprocess.run(['./start_process.sh', proc, param], capture_output=True)
    return jsonify(status='Process started', process=proc, parameter=param)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    pwd = request.form.get('password')
    if pwd is None:
        return jsonify(error='Password required'), 400
    if pwd == MASTER_PASSWORD:
        return jsonify(message='Login successful')
    return jsonify(error='Login failed'), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global MASTER_PASSWORD
    pwd = request.form.get('password')
    new_pwd = request.form.get('new_password')
    if pwd is None:
        return jsonify(error='Current password required'), 400
    if pwd != MASTER_PASSWORD:
        return jsonify(error='Authentication failed'), 401
    if not new_pwd:
        return jsonify(error='New password required'), 400
    MASTER_PASSWORD = new_pwd
    return jsonify(message='Password updated')

@app.route('/inventory/details', methods=['GET'])
def inventory_details():
    item_id = request.args.get('item_id')
    if not item_id:
        return jsonify(error='item_id required'), 400
    return jsonify(item_id=item_id, item_name='Sample Item')

@app.route('/inventory/delete', methods=['POST'])
def inventory_delete():
    item_id = request.form.get('item_id')
    if not item_id:
        return jsonify(error='item_id required'), 400
    return jsonify(message='Item deleted', item_id=item_id)

@app.route('/process/status', methods=['GET'])
def process_status():
    pid = request.args.get('process_id')
    if not pid:
        return jsonify(error='process_id required'), 400
    return jsonify(process_id=pid, status='In Progress')

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    pwd = request.form.get('password')
    config = request.form.get('config')
    if pwd is None:
        return jsonify(error='Password required'), 400
    if pwd != MASTER_PASSWORD:
        return jsonify(error='Authentication failed'), 401
    if not config:
        return jsonify(error='Config required'), 400
    return jsonify(message='Configuration updated')

@app.route('/process/logs', methods=['GET'])
def process_logs():
    pid = request.args.get('process_id')
    if not pid:
        return jsonify(error='process_id required'), 400
    return jsonify(logs=f'Logs for process {pid}')

@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    subprocess.run(['python', 'backup_inventory_data.py', fmt], capture_output=True)
    return jsonify(message='Backup started', format=fmt)

@app.route('/user/info', methods=['GET'])
def user_info():
    uid = request.args.get('user_id')
    if not uid:
        return jsonify(error='user_id required'), 400
    return jsonify(user_id=uid, name='John Smith', email='john.smith@example.com')

if __name__ == '__main__':
    app.run(debug=False)