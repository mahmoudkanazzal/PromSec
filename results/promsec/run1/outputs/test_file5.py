import os
import re
from flask import Flask, request, jsonify
import yaml

admin_password = os.getenv('ADMIN_PASSWORD', 'change_me_immediately')

def _is_safe_token(token: str) -> bool:
    return re.fullmatch(r'^[A-Za-z0-9_-]+$', token) is not None

def _is_valid_format(fmt: str) -> bool:
    return fmt in ('csv', 'json', 'xml')

def _execute_task(task: str, parameter: str) -> None:
    """Placeholder for task execution logic."""
    pass

def _export_data(fmt: str) -> None:
    """Placeholder for data export logic."""
    pass

app = Flask(__name__)

@app.route('/data/upload', methods=['POST'])
def data_upload():
    try:
        raw = request.get_data(as_text=True)
        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, dict):
            raise ValueError
        data_id = parsed.get('data_id')
        data_value = parsed.get('data_value')
        if data_id is None or data_value is None:
            raise ValueError
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    return jsonify({"status":"Data uploaded","data_id":data_id,"data_value":data_value})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    parameter = request.args.get('parameter')
    if not task or not parameter or not _is_safe_token(task) or not _is_safe_token(parameter):
        return jsonify({"status":"Error","message":"Invalid task or parameter"}), 400
    _execute_task(task, parameter)
    return jsonify({"status":"Task execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == admin_password:
        return jsonify({"status":"Access granted"})
    return jsonify({"status":"Access denied"}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    if password != admin_password:
        return jsonify({"status":"Access denied"}), 401
    new_config = request.form.get('new_config')
    if not new_config:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","new_config":new_config})

@app.route('/data/retrieve', methods=['GET'])
def data_retrieve():
    data_id = request.args.get('data_id')
    if not data_id:
        return jsonify({"status":"Error","message":"Data ID is required"}), 400
    return jsonify({"status":"Data retrieved","data_info":{"data_id":data_id,"data_value":"Sample Value"}})

@app.route('/data/delete', methods=['POST'])
def data_delete():
    data_id = request.form.get('data_id')
    if not data_id:
        return jsonify({"status":"Error","message":"Data ID is required"}), 400
    return jsonify({"status":"Data deleted","data_id":data_id})

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    global admin_password
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password != admin_password:
        return jsonify({"status":"Access denied","message":"Invalid old password"}), 401
    if new_password:
        admin_password = new_password
    return jsonify({"status":"Password changed successfully"})

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task status","task_id":task_id,"status":"Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    if password != admin_password:
        return jsonify({"status":"Access denied"}), 401
    new_setting = request.form.get('new_setting')
    if not new_setting:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting applied","new_setting":new_setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task logs","task_id":task_id,"logs":"Sample logs for task " + task_id})

@app.route('/data/export', methods=['GET'])
def data_export():
    fmt = request.args.get('format', 'csv')
    if not _is_valid_format(fmt):
        return jsonify({"status":"Error","message":"Invalid export format"}), 400
    _export_data(fmt)
    return jsonify({"status":"Data export started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User profile","profile":{"user_id":user_id,"name":"John Doe","email":"john.doe@example.com"}})

if __name__ == "__main__":
    app.run(debug=False)