import os
import re
import yaml
import subprocess
import logging
import secrets
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
if not ADMIN_PASSWORD_HASH:
    token = secrets.token_urlsafe(16)
    ADMIN_PASSWORD_HASH = generate_password_hash(token)
    logging.warning("Random admin password generated; set ADMIN_PASSWORD_HASH env variable.")

SAFE_PARAM_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")
SAFE_FORMATS = {"csv", "json"}

def is_safe_param(value: str) -> bool:
    return bool(SAFE_PARAM_RE.fullmatch(value))

def verify_admin(password: str) -> bool:
    return check_password_hash(ADMIN_PASSWORD_HASH, password)

@app.route("/task/create", methods=["POST"])
def task_create():
    data = request.get_data(as_text=True)
    if not data or len(data.encode()) > 1 * 1024 * 1024:
        return jsonify({"error": "Invalid request size"}), 400
    try:
        obj = yaml.safe_load(data)
    except yaml.YAMLError:
        return jsonify({"error": "Invalid YAML"}), 400
    if not isinstance(obj, dict):
        return jsonify({"error": "YAML must be a mapping"}), 400
    task_id = obj.get("task_id")
    task_description = obj.get("task_description")
    if task_id is None or task_description is None:
        return jsonify({"error": "Missing fields"}), 400
    return jsonify({"status": "Task created", "task_id": task_id, "task_description": task_description})

@app.route("/task/execute", methods=["GET"])
def task_execute():
    task_name = request.args.get("task_name")
    task_param = request.args.get("task_param")
    if not task_name or not task_param:
        return jsonify({"error": "Missing parameters"}), 400
    if not is_safe_param(task_name) or not is_safe_param(task_param):
        return jsonify({"error": "Invalid parameters"}), 400
    try:
        subprocess.run(
            ["sh", "execute_task.sh", task_name, task_param],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Task execution timed out"}), 504
    except Exception:
        return jsonify({"error": "Failed to start task"}), 500
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
        return jsonify({"error": "Access denied"}), 401
    new_config = request.form.get("new_config")
    if new_config is None:
        return jsonify({"error": "Missing new_config"}), 400
    return jsonify({"status": "Configuration updated", "new_config": new_config})

@app.route("/task/retrieve", methods=["GET"])
def task_retrieve():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    return jsonify({"status": "Task retrieved", "task_info": {"task_id": task_id, "description": "Sample description"}})

@app.route("/task/delete", methods=["POST"])
def task_delete():
    task_id = request.form.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    return jsonify({"status": "Task deleted", "task_id": task_id})

@app.route("/admin/change_password", methods=["POST"])
def admin_change_password():
    global ADMIN_PASSWORD_HASH
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    if not new_password:
        return jsonify({"error": "New password cannot be empty"}), 400
    if not check_password_hash(ADMIN_PASSWORD_HASH, old_password):
        return jsonify({"error": "Access denied", "message": "Invalid old password"}), 401
    ADMIN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({"status": "Password changed successfully"})

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
        return jsonify({"error": "Access denied"}), 401
    new_setting = request.form.get("new_setting")
    if new_setting is None:
        return jsonify({"error": "Missing new_setting"}), 400
    return jsonify({"status": "Setting applied", "new_setting": new_setting})

@app.route("/task/logs", methods=["GET"])
def task_logs():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": "Sample log content"})

@app.route("/task/export", methods=["GET"])
def task_export():
    fmt = request.args.get("format", "csv").lower()
    if fmt not in SAFE_FORMATS:
        return jsonify({"error": "Invalid format"}), 400
    try:
        subprocess.run(
            ["python3", "export_tasks.py", fmt],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Export operation timed out"}), 504
    except Exception:
        return jsonify({"error": "Failed to start export"}), 500
    return jsonify({"status": "Task export started"})

@app.route("/user/profile", methods=["GET"])
def user_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    return jsonify({"status": "User profile", "profile": {"user_id": user_id, "name": "Jane Doe", "email": "jane.doe@example.com"}})

@app.route("/task/update", methods=["POST"])
def task_update():
    task_id = request.form.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    new_description = request.form.get("new_description", "")
    return jsonify({"status": "Task updated", "task_id": task_id, "new_description": new_description})

@app.route("/task/assign", methods=["POST"])
def task_assign():
    task_id = request.form.get("task_id")
    user_id = request.form.get("user_id")
    if not task_id or not user_id:
        return jsonify({"error": "Missing parameters"}), 400
    return jsonify({"status": "Task assigned", "task_id": task_id, "user_id": user_id})

if __name__ == "__main__":
    app.run(debug=False)