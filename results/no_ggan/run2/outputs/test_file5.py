import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DEFAULT_ADMIN_PASSWORD = "admin1234"
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH") or generate_password_hash(DEFAULT_ADMIN_PASSWORD)

def verify_admin(password: str) -> bool:
    return check_password_hash(ADMIN_PASSWORD_HASH, password)

ALLOWED_TASKS = {"backup", "cleanup", "report"}
PARAMETER_PATTERN = re.compile(r'^[\w\-\.]+$')
ALLOWED_EXPORT_FORMATS = {"csv", "json", "xml"}

@app.route("/data/upload", methods=["POST"])
def data_upload():
    raw = request.get_data(as_text=True)
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"error": "Invalid YAML"}), 400
    if not isinstance(parsed, dict):
        return jsonify({"error": "YAML must be a mapping"}), 400
    data_id = parsed.get("data_id")
    data_value = parsed.get("data_value")
    if not data_id or not data_value:
        return jsonify({"error": "Missing data_id or data_value"}), 400
    return jsonify({"status": "Data uploaded", "data_id": data_id, "data_value": data_value})

@app.route("/task/execute", methods=["GET"])
def task_execute():
    task = request.args.get("task")
    parameter = request.args.get("parameter")
    if task not in ALLOWED_TASKS:
        return jsonify({"error": "Invalid task"}), 400
    if parameter is not None and not PARAMETER_PATTERN.fullmatch(parameter):
        return jsonify({"error": "Invalid parameter"}), 400
    cmd = ["sh", "execute_task.sh", task]
    if parameter:
        cmd.append(parameter)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"error": "Task execution failed"}), 500
    return jsonify({"status": "Task execution started"})

@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password", "")
    if verify_admin(password):
        return jsonify({"status": "Access granted"})
    return jsonify({"status": "Access denied"}), 401

@app.route("/admin/configure", methods=["POST"])
def admin_configure():
    password = request.form.get("password", "")
    if not verify_admin(password):
        return jsonify({"status": "Access denied"}), 401
    new_config = request.form.get("new_config")
    if not new_config:
        return jsonify({"error": "Missing new_config"}), 400
    return jsonify({"status": "Configuration updated", "new_config": new_config})

@app.route("/data/retrieve", methods=["GET"])
def data_retrieve():
    data_id = request.args.get("data_id")
    if not data_id:
        return jsonify({"error": "Missing data_id"}), 400
    return jsonify({"status": "Data retrieved", "data": {"data_id": data_id, "data_value": "Sample Value"}})

@app.route("/data/delete", methods=["POST"])
def data_delete():
    data_id = request.form.get("data_id")
    if not data_id:
        return jsonify({"error": "Missing data_id"}), 400
    return jsonify({"status": "Data deleted", "data_id": data_id})

@app.route("/admin/change_password", methods=["POST"])
def admin_change_password():
    return jsonify({"status": "Error", "message": "Password change not supported"}), 403

@app.route("/task/status", methods=["GET"])
def task_status():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    return jsonify({"status": "Task status", "task_id": task_id, "state": "Running"})

@app.route("/admin/settings", methods=["POST"])
def admin_settings():
    password = request.form.get("password", "")
    if not verify_admin(password):
        return jsonify({"status": "Access denied"}), 401
    new_setting = request.form.get("new_setting")
    if not new_setting:
        return jsonify({"error": "Missing new_setting"}), 400
    return jsonify({"status": "Setting applied", "new_setting": new_setting})

@app.route("/task/logs", methods=["GET"])
def task_logs():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": f"Sample logs for task {task_id}"})

@app.route("/data/export", methods=["GET"])
def data_export():
    export_format = request.args.get("format", "csv")
    if export_format not in ALLOWED_EXPORT_FORMATS:
        return jsonify({"error": "Invalid export format"}), 400
    cmd = ["python3", "export_data.py", export_format]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"error": "Data export failed"}), 500
    return jsonify({"status": "Data export started"})

@app.route("/user/profile", methods=["GET"])
def user_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    return jsonify({"status": "User profile", "profile": {"user_id": user_id, "name": "John Doe", "email": "john.doe@example.com"}})

if __name__ == "__main__":
    app.run(debug=False)