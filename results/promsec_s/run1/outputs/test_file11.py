import os
import yaml
import hmac
from flask import Flask, request, jsonify

class SubprocessStub:
    @staticmethod
    def run(command, *args, **kwargs):
        if not isinstance(command, (list, tuple)):
            raise ValueError("Command must be a list or tuple")
        return None

master_password = os.getenv('MASTER_PASSWORD')
if master_password is None:
    raise RuntimeError("MASTER_PASSWORD environment variable not set")

app = Flask(__name__)

@app.route('/service/create', methods=['POST'])
def service_create():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict) or 'service_id' not in data or 'service_name' not in data:
        return jsonify({"status":"Error","message":"Missing service information"}), 400
    return jsonify({"status":"Service created","service_id":data['service_id'],"service_name":data['service_name']})

@app.route('/operations/start', methods=['GET'])
def operations_start():
    operation = request.args.get('operation')
    if not operation:
        return jsonify({"status":"Error","message":"Invalid operation"}), 400
    parameter = request.args.get('parameter', '')
    whitelist = ["backup","cleanup","restart"]
    if operation not in whitelist:
        return jsonify({"status":"Error","message":"Invalid operation"}), 400
    SubprocessStub.run(["sh","run_operation.sh", operation, parameter])
    return jsonify({"status":"Operation started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, master_password):
        return jsonify({"status":"Login successful"})
    return jsonify({"status":"Login failed"}), 401

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global master_password
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if not hmac.compare_digest(password, master_password):
        return jsonify({"status":"Login failed"}), 401
    if not new_password:
        return jsonify({"status":"Error","message":"Invalid new password"}), 400
    master_password = new_password
    return jsonify({"status":"Password updated"})

@app.route('/service/details', methods=['GET'])
def service_details():
    service_id = request.args.get('service_id')
    if not service_id:
        return jsonify({"status":"Error","message":"Service ID is required"}), 400
    return jsonify({"status":"Service details retrieved","service":{"service_id":service_id,"service_name":"Example Service"}})

@app.route('/service/delete', methods=['POST'])
def service_delete():
    service_id = request.form.get('service_id')
    if not service_id:
        return jsonify({"status":"Error","message":"Service ID is required"}), 400
    return jsonify({"status":"Service deleted","service_id":service_id})

@app.route('/operations/status', methods=['GET'])
def operations_status():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify({"status":"Error","message":"Operation ID is required"}), 400
    return jsonify({"status":"Operation status","operation_id":operation_id,"operation_state":"In Progress"})

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    config = request.form.get('config', '')
    if not hmac.compare_digest(password, master_password):
        return jsonify({"status":"Access denied"}), 401
    if not config:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","config":config})

@app.route('/operations/logs', methods=['GET'])
def operations_logs():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify({"status":"Error","message":"Operation ID is required"}), 400
    return jsonify({"status":"Operation logs","operation_id":operation_id,"logs":"Logs for operation " + operation_id})

@app.route('/data/backup', methods=['GET'])
def data_backup():
    backup_format = request.args.get('format', 'json')
    SubprocessStub.run(["python","backup_data.py", backup_format])
    return jsonify({"status":"Data backup started"})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User information retrieved","user_info":{"user_id":user_id,"name":"Alice Johnson","email":"alice.johnson@example.com"}})

if __name__ == '__main__':
    app.run(debug=False)