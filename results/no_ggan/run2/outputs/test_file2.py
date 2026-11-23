from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import threading
import re

app = Flask(__name__)
SECRET_TOKEN = os.getenv("APP_SECRET_TOKEN", "secure_token_2024")
SAFE_INPUT_RE = re.compile(r'^[\w\-]+$')
ALLOWED_BACKUP_FORMATS = {"json", "yaml", "csv"}

def _is_safe_input(value: str) -> bool:
    return bool(SAFE_INPUT_RE.fullmatch(value))

def _run_subprocess(command):
    subprocess.run(command, check=False)

@app.route("/config/upload", methods=["POST"])
def config_upload():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"error": "Invalid YAML"}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "YAML must be a mapping"}), 400
    config_name = data.get("config_name")
    config_value = data.get("config_value")
    if not config_name or not config_value:
        return jsonify({"error": "Missing config_name or config_value"}), 400
    return jsonify({"status": "Configuration uploaded", "config_name": config_name, "config_value": config_value})

@app.route("/task/execute", methods=["GET"])
def task_execute():
    task = request.args.get("task")
    param = request.args.get("param")
    if not task or not param or not _is_safe_input(task) or not _is_safe_input(param):
        return jsonify({"error": "Invalid task or param"}), 400
    command = ["sh", "execute_task.sh", task, param]
    thread = threading.Thread(target=_run_subprocess, args=(command,), daemon=True)
    thread.start()
    return jsonify({"status": "Task execution started"})

@app.route("/admin/verify", methods=["POST"])
def admin_verify():
    token = request.form.get("token")
    if token == SECRET_TOKEN:
        return jsonify({"status": "Verification successful"})
    return jsonify({"status": "Verification failed"}), 401

@app.route("/admin/update_token", methods=["POST"])
def admin_update_token():
    global SECRET_TOKEN
    current_token = request.form.get("current_token")
    new_token = request.form.get("new_token")
    if current_token != SECRET_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    if not new_token:
        return jsonify({"error": "New token required"}), 400
    SECRET_TOKEN = new_token
    return jsonify({"status": "Token updated"})

@app.route("/config/retrieve", methods=["GET"])
def config_retrieve():
    config_name = request.args.get("config_name")
    if not config_name:
        return jsonify({"error": "config_name required"}), 400
    return jsonify({"status": "Configuration retrieved", "config": {"name": config_name, "value": "placeholder"}})

@app.route("/config/delete", methods=["POST"])
def config_delete():
    config_name = request.form.get("config_name")
    if not config_name:
        return jsonify({"error": "config_name required"}), 400
    return jsonify({"status": "Configuration deleted", "config_name": config_name})

@app.route("/task/status", methods=["GET"])
def task_status():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "task_id required"}), 400
    return jsonify({"status": "Task status", "task_id": task_id, "state": "Running"})

@app.route("/admin/settings", methods=["POST"])
def admin_settings():
    token = request.form.get("token")
    if token != SECRET_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    setting = request.form.get("setting")
    if not setting:
        return jsonify({"error": "setting required"}), 400
    return jsonify({"status": "Setting updated", "setting": setting})

@app.route("/task/logs", methods=["GET"])
def task_logs():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "task_id required"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": "placeholder log content"})

@app.route("/backup/data", methods=["GET"])
def backup_data():
    fmt = request.args.get("format", "json").lower()
    if fmt not in ALLOWED_BACKUP_FORMATS:
        return jsonify({"error": "Invalid format"}), 400
    command = ["python3", "backup_data.py", fmt]
    thread = threading.Thread(target=_run_subprocess, args=(command,), daemon=True)
    thread.start()
    return jsonify({"status": "Data backup started"})

@app.route("/user/profile", methods=["GET"])
def user_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    profile = {"user_id": user_id, "name": "Michael Brown", "email": "michael.brown@example.com"}
    return jsonify({"status": "User profile retrieved", "profile": profile})

if __name__ == "__main__":
    app.run(debug=False)