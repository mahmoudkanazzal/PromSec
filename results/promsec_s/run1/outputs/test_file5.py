import os
import yaml
import sys
import importlib
from flask import Flask, request, jsonify

app = Flask(__name__)
admin_password = os.getenv('ADMIN_PASSWORD', 'admin1234')

def check_admin(password):
    return password == admin_password

def _run_export(export_format):
    whitelist = {'csv', 'json', 'xml'}
    if export_format not in whitelist:
        raise ValueError(f'Unsupported format: {export_format}')
    try:
        module = importlib.import_module('export_data')
        if hasattr(module, 'main') and callable(module.main):
            module.main(export_format)
        elif hasattr(module, 'run') and callable(module.run):
            module.run(export_format)
        else:
            raise RuntimeError('export_data module lacks callable entry point')
    except Exception as e:
        raise RuntimeError('Export failed') from e

@app.route('/data/upload', methods=['POST'])
def data_upload():
    raw = request.get_data(as_text=True)
    try:
        parsed = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(parsed, dict):
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    data_id = parsed.get('data_id')
    data_value = parsed.get('data_value')
    if data_id is None or data_value is None:
        return jsonify({"status":"Error","message":"Missing data information"}), 400
    return jsonify({"status":"Data uploaded","data_id": data_id,"data_value": data_value})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task = request.args.get('task')
    parameter = request.args.get('parameter')
    allowed = {'backup', 'cleanup'}
    if task not in allowed:
        return jsonify({"status":"Error","message":"Invalid task"}), 400
    return jsonify({"status":"Task execution started","task": task,"parameter": parameter})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if check_admin(password):
        return jsonify({"status":"Access granted"})
    return jsonify({"status":"Access denied"}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password')
    if not check_admin(password):
        return jsonify({"status":"Access denied"}), 401
    new_config = request.form.get('new_config')
    if new_config is None:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","new_config": new_config})

@app.route('/data/retrieve', methods=['GET'])
def data_retrieve():
    data_id = request.args.get('data_id')
    if not data_id:
        return jsonify({"status":"Error","message":"Data ID is required"}), 400
    return jsonify({"status":"Data retrieved","data_info":{"data_id": data_id,"data_value":"Sample Value"}})

@app.route('/data/delete', methods=['POST'])
def data_delete():
    data_id = request.form.get('data_id')
    if not data_id:
        return jsonify({"status":"Error","message":"Data ID is required"}), 400
    return jsonify({"status":"Data deleted","data_id": data_id})

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    global admin_password
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == admin_password:
        admin_password = new_password
        return jsonify({"status":"Password changed successfully"})
    return jsonify({"status":"Access denied","message":"Invalid old password"}), 401

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task status","task_id": task_id,"status":"Running"})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    if not check_admin(password):
        return jsonify({"status":"Access denied"}), 401
    new_setting = request.form.get('new_setting')
    if new_setting is None:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting applied","new_setting": new_setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task logs","task_id": task_id,"logs":"Sample logs for task " + task_id})

@app.route('/data/export', methods=['GET'])
def data_export():
    export_format = request.args.get('format', 'csv')
    try:
        _run_export(export_format)
    except ValueError as ve:
        return jsonify({"status":"Error","message": str(ve)}), 400
    except RuntimeError as re:
        return jsonify({"status":"Error","message": str(re)}), 500
    return jsonify({"status":"Data export started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User profile","profile":{"user_id": user_id,"name":"John Doe","email":"john.doe@example.com"}})

if __name__ == '__main__':
    app.run(debug=False)