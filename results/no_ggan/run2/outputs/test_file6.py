import os
import re
import sys
import subprocess
import threading
from flask import Flask, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import yaml

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

_admin_hash_lock = threading.Lock()
_admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")
if not _admin_password_hash:
    raise RuntimeError("Environment variable ADMIN_PASSWORD_HASH is required")

def is_admin_password(password: str) -> bool:
    with _admin_hash_lock:
        return check_password_hash(_admin_password_hash, password)

def _error(message, code):
    return jsonify({"status":"Error","message":message}), code

task_name_pattern = re.compile(r"^[\w\-]+$")
task_param_pattern = re.compile(r"^[\w\-.]*$")
task_id_pattern = re.compile(r"^[\w\-]+$")
format_allowed = {"csv","json","xml"}

@app.route("/task/create", methods=["POST"])
def task_create():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return _error("Invalid YAML", 400)
    if not isinstance(data, dict):
        return _error("YAML must be a mapping", 400)
    task_id = data.get("task_id")
    task_description = data.get("task_description")
    if not task_id or not task_description:
        return _error("Missing task_id or task_description", 400)
    return jsonify({"status":"Task created","task_id":task_id,"task_description":task_description}), 200

@app.route("/task/execute", methods=["GET"])
def task_execute():
    task_name = request.args.get("task_name")
    task_param = request.args.get("task_param", "")
    if not task_name or not task_name_pattern.fullmatch(task_name):
        return _error("Invalid or missing task_name", 400)
    if task_param and not task_param_pattern.fullmatch(task_param):
        return _error("Invalid task_param", 400)
    script_path = "./execute_task.sh"
    if not (os.path.isfile(script_path) and os.access(script_path, os.X_OK)):
        return _error("Script not found or not executable", 500)
    cmd = [script_path, task_name, task_param]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"status":"Error","message":"Task execution failed","details":e.stderr}), 500
    return jsonify({"status":"Task execution started"}), 200

@app.route("/task/retrieve", methods=["GET"])
def task_retrieve():
    task_id = request.args.get("task_id")
    if not task_id:
        return _error("Missing task_id", 400)
    return jsonify({"status":"Task retrieved","task_id":task_id,"task_description":"Placeholder description"}), 200

@app.route("/task/delete", methods=["POST"])
def task_delete():
    task_id = request.form.get("task_id")
    if not task_id:
        return _error("Missing task_id", 400)
    return jsonify({"status":"Task deleted","task_id":task_id}), 200

@app.route("/task/status", methods=["GET"])
def task_status():
    task_id = request.args.get("task_id")
    if not task_id:
        return _error("Missing task_id", 400)
    return jsonify({"status":"Task status","task_id":task_id,"status_detail":"Running"}), 200

@app.route("/task/logs", methods=["GET"])
def task_logs():
    task_id = request.args.get("task_id")
    if not task_id:
        return _error("Missing task_id", 400)
    return jsonify({"status":"Task logs","task_id":task_id,"logs":f"Sample logs for task {task_id}"}), 200

@app.route("/task/export", methods=["GET"])
def task_export():
    export_format = request.args.get("format", "csv")
    if export_format not in format_allowed:
        return _error("Invalid format", 400)
    script_path = "./export_tasks.py"
    if not os.path.isfile(script_path):
        return _error("Export script not found", 500)
    cmd = [sys.executable, script_path, export_format]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"status":"Error","message":"Export failed","details":e.stderr}), 500
    return jsonify({"status":"Task export started"}), 200

@app.route("/task/update", methods=["POST"])
def task_update():
    task_id = request.form.get("task_id")
    new_description = request.form.get("new_description")
    if not task_id:
        return _error("Missing task_id", 400)
    return jsonify({"status":"Task updated","task_id":task_id,"new_description":new_description}), 200

@app.route("/task/assign", methods=["POST"])
def task_assign():
    task_id = request.form.get("task_id")
    user_id = request.form.get("user_id")
    if not task_id or not user_id:
        return _error("Missing task_id or user_id", 400)
    return jsonify({"status":"Task assigned","task_id":task_id,"user_id":user_id}), 200

@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password")
    if password is None:
        return _error("Missing password", 400)
    if is_admin_password(password):
        return jsonify({"status":"Access granted"}), 200
    return jsonify({"status":"Access denied"}), 401

@app.route("/admin/configure", methods=["POST"])
def admin_configure():
    password = request.form.get("password")
    new_config = request.form.get("new_config")
    if password is None or new_config is None:
        return _error("Missing password or new_config", 400)
    if not is_admin_password(password):
        return jsonify({"status":"Access denied"}), 401
    return jsonify({"status":"Configuration updated","new_config":new_config}), 200

@app.route("/admin/change_password", methods=["POST"])
def admin_change_password():
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    if old_password is None or new_password is None:
        return _error("Missing old_password or new_password", 400)
    if not is_admin_password(old_password):
        return jsonify({"status":"Access denied"}), 401
    new_hash = generate_password_hash(new_password)
    with _admin_hash_lock:
        global _admin_password_hash
        _admin_password_hash = new_hash
        os.environ["ADMIN_PASSWORD_HASH"] = new_hash
    return jsonify({"status":"Password changed successfully"}), 200

@app.route("/admin/settings", methods=["POST"])
def admin_settings():
    password = request.form.get("password")
    new_setting = request.form.get("new_setting")
    if password is None or new_setting is None:
        return _error("Missing password or new_setting", 400)
    if not is_admin_password(password):
        return jsonify({"status":"Access denied"}), 401
    return jsonify({"status":"Setting applied","new_setting":new_setting}), 200

@app.route("/user/profile", methods=["GET"])
def user_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return _error("Missing user_id", 400)
    profile = {"user_id":user_id,"name":"Jane Doe","email":"jane.doe@example.com"}
    return jsonify({"status":"User profile","profile":profile}), 200

if __name__ == "__main__":
    app.run(debug=False)