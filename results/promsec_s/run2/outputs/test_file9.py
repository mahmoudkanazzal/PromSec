import os
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)
app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD', 'admin_pass_2024')


def _run_job(job_name, parameter):
    whitelist = {'backup', 'cleanup', 'report'}
    if job_name not in whitelist:
        return False
    return True


def _export_data(export_format):
    whitelist = {'json', 'csv', 'xml'}
    if export_format not in whitelist:
        return False
    return True


@app.route('/config/add', methods=['POST'])
def config_add():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    config_id = data.get('config_id')
    config_value = data.get('config_value')
    if config_id is None or config_value is None:
        return jsonify({"status": "Error", "message": "Missing configuration information"}), 400
    return jsonify({"status": "Configuration added", "config_id": config_id, "config_value": config_value})


@app.route('/job/execute', methods=['GET'])
def job_execute():
    job_name = request.args.get('job_name', '')
    parameter = request.args.get('parameter', '')
    _run_job(job_name, parameter)
    return jsonify({"status": "Job execution started"})


@app.route('/auth/login', methods=['POST'])
def auth_login():
    password = request.form.get('password', '')
    if password == app.config['ADMIN_PASSWORD']:
        return jsonify({"status": "Login successful"})
    return jsonify({"status": "Login failed"}), 401


@app.route('/auth/update_password', methods=['POST'])
def auth_update_password():
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if password != app.config['ADMIN_PASSWORD']:
        return jsonify({"status": "Login failed"}), 401
    if not new_password:
        return jsonify({"status": "Error", "message": "Invalid new password"}), 400
    app.config['ADMIN_PASSWORD'] = new_password
    return jsonify({"status": "Password updated"})


@app.route('/config/get', methods=['GET'])
def config_get():
    config_id = request.args.get('config_id')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400
    return jsonify({"status": "Configuration retrieved", "config": {"config_id": config_id, "config_value": "Sample Value"}})


@app.route('/config/remove', methods=['POST'])
def config_remove():
    config_id = request.form.get('config_id')
    if not config_id:
        return jsonify({"status": "Error", "message": "Configuration ID is required"}), 400
    return jsonify({"status": "Configuration removed", "config_id": config_id})


@app.route('/job/status', methods=['GET'])
def job_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400
    return jsonify({"status": "Job status", "job_id": job_id, "status": "In Progress"})


@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password', '')
    setting = request.form.get('setting')
    if password != app.config['ADMIN_PASSWORD']:
        return jsonify({"status": "Access denied"}), 401
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400
    return jsonify({"status": "Setting updated", "setting": setting})


@app.route('/job/logs', methods=['GET'])
def job_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"status": "Error", "message": "Job ID is required"}), 400
    logs = "Logs for job " + job_id
    return jsonify({"status": "Job logs", "job_id": job_id, "logs": logs})


@app.route('/data/export', methods=['GET'])
def data_export():
    export_format = request.args.get('format', 'json')
    _export_data(export_format)
    return jsonify({"status": "Data export started"})


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    return jsonify({"status": "User information retrieved", "user_info": {"user_id": user_id, "name": "John Doe", "email": "john.doe@example.com"}})


if __name__ == '__main__':
    app.run(debug=False)