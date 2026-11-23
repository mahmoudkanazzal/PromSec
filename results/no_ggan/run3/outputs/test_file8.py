import os
import re
import hmac
import yaml  # use safe_load to avoid arbitrary code execution
import subprocess
import functools
from flask import Flask, request, jsonify

app = Flask(__name__)

# Secret key from environment; change placeholder in production
SECRET_KEY = os.getenv("SECRET_KEY", "default_insecure_key_change_me")
app.secret_key = SECRET_KEY

# Allow only alphanumeric, underscore, hyphen
SAFE_PATTERN = re.compile(r'^[\w\-]+$')

def constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1, val2)

def admin_required(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        key = None
        if request.is_json:
            key = request.json.get("key")
        if not key:
            key = request.headers.get("X-Admin-Key")
        if not key:
            key = request.form.get("key")
        if not key or not constant_time_compare(key, SECRET_KEY):
            return jsonify({"status": "Authentication failed"}), 401
        return view_func(*args, **kwargs)
    return wrapper

def safe_subprocess(command: list):
    try:
        subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        pass  # In real apps, log the error

@app.route("/user/add", methods=["POST"])
def add_user():
    raw_data = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw_data)  # safe_load prevents code execution
    except yaml.YAMLError:
        return jsonify({"error": "Invalid YAML"}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid data format"}), 400
    if "id" not in data or "name" not in data:
        return jsonify({"error": "Missing 'id' or 'name'"}), 400
    return jsonify({"status": "User added"}), 200

@app.route("/system/start_task", methods=["GET"])
def start_task():
    task = request.args.get("task")
    argument = request.args.get("argument")
    if not task or not argument:
        return jsonify({"error": "Missing parameters"}), 400
    if not SAFE_PATTERN.fullmatch(task) or not SAFE_PATTERN.fullmatch(argument):
        return jsonify({"error": "Invalid characters in parameters"}), 400
    safe_subprocess(['bash', 'start_task.sh', task, argument])
    return jsonify({"status": "Task started"}), 200

@app.route("/admin/authenticate", methods=["POST"])
def admin_authenticate():
    key = None
    if request.is_json:
        key = request.json.get("key")
    if not key:
        key = request.headers.get("X-Admin-Key")
    if not key:
        key = request.form.get("key")
    if not key or not constant_time_compare(key, SECRET_KEY):
        return jsonify({"status": "Authentication failed"}), 401
    return jsonify({"status": "Authenticated"}), 200

@app.route("/admin/update_config", methods=["POST"])
@admin_required
def update_config():
    new_config = request.form.get("new_config")
    if not new_config:
        return jsonify({"error": "Missing new_config"}), 400
    return jsonify({"status": "Configuration updated"}), 200

@app.route("/user/fetch", methods=["GET"])
def fetch_user():
    user_id = request.args.get("id")
    if not user_id:
        return jsonify({"error": "Missing id"}), 400
    return jsonify({"id": user_id, "name": "Sample User"}), 200

@app.route("/user/delete", methods=["POST"])
def delete_user():
    user_id = request.form.get("id")
    if not user_id:
        return jsonify({"error": "Missing id"}), 400
    return jsonify({"status": "User deleted"}), 200

@app.route("/admin/change_key", methods=["POST"])
@admin_required
def change_key():
    return jsonify({"status": "Key change not permitted"}), 403

@app.route("/task/status", methods=["GET"])
def task_status():
    task_id = request.args.get("id")
    if not task_id:
        return jsonify({"error": "Missing id"}), 400
    return jsonify({"id": task_id, "status": "Running"}), 200

@app.route("/admin/set_preference", methods=["POST"])
@admin_required
def set_preference():
    pref = request.form.get("preference")
    if not pref:
        return jsonify({"error": "Missing preference"}), 400
    return jsonify({"status": "Preference set", "preference": pref}), 200

@app.route("/logs/view", methods=["GET"])
def view_logs():
    log_id = request.args.get("id")
    if not log_id:
        return jsonify({"error": "Missing id"}), 400
    return jsonify({"id": log_id, "log": "Placeholder log text"}), 200

@app.route("/data/export", methods=["GET"])
def export_data():
    export_type = request.args.get("type", "json")
    if not SAFE_PATTERN.fullmatch(export_type):
        return jsonify({"error": "Invalid export type"}), 400
    safe_subprocess(['python3', 'export_data.py', export_type])
    return jsonify({"status": "Data export started"}), 200

@app.route("/user/details", methods=["GET"])
def user_details():
    user_id = request.args.get("id")
    if not user_id:
        return jsonify({"error": "Missing id"}), 400
    return jsonify({
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }), 200

@app.route("/task/execute", methods=["GET"])
def execute_task():
    task = request.args.get("task")
    argument = request.args.get("argument")
    if not task or not argument:
        return jsonify({"error": "Missing parameters"}), 400
    if not SAFE_PATTERN.fullmatch(task) or not SAFE_PATTERN.fullmatch(argument):
        return jsonify({"error": "Invalid characters in parameters"}), 400
    safe_subprocess(['bash', 'execute_task.sh', task, argument])
    return jsonify({"status": "Task execution started"}), 200

@app.route("/task/logs", methods=["GET"])
def task_logs():
    task_id = request.args.get("id")
    if not task_id:
        return jsonify({"error": "Missing id"}), 400
    return jsonify({"id": task_id, "log": "Placeholder task log"}), 200

if __name__ == "__main__":
    # Debug must remain disabled in production
    app.run(debug=False)