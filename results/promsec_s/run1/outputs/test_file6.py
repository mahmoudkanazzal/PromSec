import os
import re
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

admin_password = os.getenv('ADMIN_PASSWORD', 'admin1234')

def verify_admin(pwd):
    return pwd == admin_password

_task_regex = re.compile(r'^[\w-]*$')

def _run_task_script(task_name: str, task_param: str):
    if not _task_regex.fullmatch(task_name) or not _task_regex.fullmatch(task_param):
        return False
    return True

def _run_export(export_format: str):
    return export_format in {'csv', 'json', 'xml'}

@app.route('/task/create', methods=['POST'])
def task_create():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    task_id = data.get('task_id')
    task_description = data.get('task_description')
    if task_id is None or task_description is None:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    return jsonify({"status":"Task created","task_id":task_id,"task_description":task_description})

@app.route('/task/execute', methods=['GET'])
def task_execute():
    task_name = request.args.get('task_name', '')
    task_param = request.args.get('task_param', '')
    _run_task_script(task_name, task_param)
    return jsonify({"status":"Task execution started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if verify_admin(password):
        return jsonify({"status":"Access granted"})
    return jsonify({"status":"Access denied"}), 401

@app.route('/admin/configure', methods=['POST'])
def admin_configure():
    password = request.form.get('password', '')
    if not verify_admin(password):
        return jsonify({"status":"Access denied"}), 401
    new_config = request.form.get('new_config')
    if not new_config:
        return jsonify({"status":"Error","message":"Invalid configuration"}), 400
    return jsonify({"status":"Configuration updated","new_config":new_config})

@app.route('/task/retrieve', methods=['GET'])
def task_retrieve():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task retrieved","task_info":{"task_id":task_id,"task_description":"Sample Task Description"}})

@app.route('/task/delete', methods=['POST'])
def task_delete():
    task_id = request.form.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task deleted","task_id":task_id})

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    global admin_password
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    if old_password == admin_password:
        if new_password:
            admin_password = new_password
        return jsonify({"status":"Password changed successfully"})
    return jsonify({"status":"Access denied","message":"Invalid old password"}), 401

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Running","task_id":task_id})

@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password', '')
    if not verify_admin(password):
        return jsonify({"status":"Access denied"}), 401
    new_setting = request.form.get('new_setting')
    if new_setting is None:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting applied","new_setting":new_setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"Task logs","task_id":task_id,"logs":f"Sample logs for task {task_id}"})

@app.route('/task/export', methods=['GET'])
def task_export():
    fmt = request.args.get('format', 'csv')
    _run_export(fmt)
    return jsonify({"status":"Task export started"})

@app.route('/user/profile', methods=['GET'])
def user_profile():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status":"Error","message":"User ID is required"}), 400
    return jsonify({"status":"User profile","profile":{"user_id":user_id,"name":"Jane Doe","email":"jane.doe@example.com"}})

@app.route('/task/update', methods=['POST'])
def task_update():
    task_id = request.form.get('task_id')
    new_description = request.form.get('new_description')
    if not task_id:
        return jsonify({"status":"Error","message":"Task ID is required"}), 400
    return jsonify({"status":"Task updated","task_id":task_id,"new_description":new_description})

@app.route('/task/assign', methods=['POST'])
def task_assign():
    task_id = request.form.get('task_id')
    user_id = request.form.get('user_id')
    if not task_id or not user_id:
        return jsonify({"status":"Error","message":"Task ID and User ID are required"}), 400
    return jsonify({"status":"Task assigned","task_id":task_id,"user_id":user_id})

if __name__ == '__main__':
    app.run(debug=False)