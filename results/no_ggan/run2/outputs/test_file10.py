import os
import re
import subprocess
import threading
import yaml
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

ADMIN_HASH_FILE = "admin_password.hash"
ALLOWED_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
ALLOWED_EXPORT_FORMATS = {"json", "csv", "xml"}

_hash_lock = threading.Lock()
_admin_password_hash = None

def _load_admin_hash():
    if os.path.isfile(ADMIN_HASH_FILE):
        with open(ADMIN_HASH_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    env_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if env_hash:
        return env_hash.strip()
    return generate_password_hash("event_admin_2024")

def _save_admin_hash(new_hash):
    with open(ADMIN_HASH_FILE, "w", encoding="utf-8") as f:
        f.write(new_hash)

def _get_admin_hash():
    global _admin_password_hash
    with _hash_lock:
        if _admin_password_hash is None:
            _admin_password_hash = _load_admin_hash()
        return _admin_password_hash

def _set_admin_hash(new_hash):
    global _admin_password_hash
    with _hash_lock:
        _admin_password_hash = new_hash
        _save_admin_hash(new_hash)

def _is_valid_id(value):
    return isinstance(value, str) and ALLOWED_ID_PATTERN.fullmatch(value) is not None

@app.route("/event/add", methods=["POST"])
def add_event():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"error": "Invalid YAML"}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "YAML must be a mapping"}), 400
    event_id = data.get("event_id")
    event_name = data.get("event_name")
    event_date = data.get("event_date")
    if not event_id or not isinstance(event_id, str):
        return jsonify({"error": "Missing or empty event_id"}), 400
    if not event_name or not isinstance(event_name, str):
        return jsonify({"error": "Missing or empty event_name"}), 400
    if not event_date or not isinstance(event_date, str):
        return jsonify({"error": "Missing or empty event_date"}), 400
    return jsonify({
        "status": "Event added",
        "event_id": event_id,
        "event_name": event_name,
        "event_date": event_date
    })

@app.route("/event/start", methods=["GET"])
def start_event():
    event_id = request.args.get("event_id", "")
    task = request.args.get("task", "")
    if not _is_valid_id(event_id):
        return jsonify({"error": "Invalid event_id"}), 400
    if not _is_valid_id(task):
        return jsonify({"error": "Invalid task"}), 400
    try:
        subprocess.run(["sh", "start_event.sh", event_id, task], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Failed to start event"}), 500
    return jsonify({"status": "Event started"})

@app.route("/auth/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    admin_hash = _get_admin_hash()
    if check_password_hash(admin_hash, password):
        return jsonify({"status": "Login successful"})
    return jsonify({"error": "Login failed"}), 401

@app.route("/auth/update_password", methods=["POST"])
def update_password():
    current = request.form.get("password", "")
    new_password = request.form.get("new_password", "")
    if not new_password:
        return jsonify({"error": "New password required"}), 400
    admin_hash = _get_admin_hash()
    if not check_password_hash(admin_hash, current):
        return jsonify({"error": "Current password invalid"}), 401
    new_hash = generate_password_hash(new_password)
    _set_admin_hash(new_hash)
    return jsonify({"status": "Password updated"})

@app.route("/event/get", methods=["GET"])
def get_event():
    event_id = request.args.get("event_id")
    if not event_id:
        return jsonify({"error": "Missing event_id"}), 400
    return jsonify({
        "status": "Event retrieved",
        "event_id": event_id,
        "event_name": "Sample Event",
        "event_date": "2024-01-01"
    })

@app.route("/event/remove", methods=["POST"])
def remove_event():
    event_id = request.form.get("event_id", "")
    if not event_id:
        return jsonify({"error": "Missing event_id"}), 400
    return jsonify({"status": "Event removed", "event_id": event_id})

@app.route("/task/status", methods=["GET"])
def task_status():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    return jsonify({
        "status": "Task status",
        "task_id": task_id,
        "status_detail": "In Progress"
    })

@app.route("/auth/settings", methods=["POST"])
def auth_settings():
    password = request.form.get("password", "")
    setting = request.form.get("setting")
    if setting is None:
        return jsonify({"error": "Missing setting"}), 400
    admin_hash = _get_admin_hash()
    if not check_password_hash(admin_hash, password):
        return jsonify({"error": "Login failed"}), 401
    return jsonify({"status": "Setting updated", "setting": setting})

@app.route("/task/logs", methods=["GET"])
def task_logs():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    return jsonify({
        "status": "Task logs",
        "task_id": task_id,
        "logs": f"Logs for task {task_id}"
    })

@app.route("/data/export", methods=["GET"])
def data_export():
    fmt = request.args.get("format", "json").lower()
    if fmt not in ALLOWED_EXPORT_FORMATS:
        return jsonify({"error": "Invalid format"}), 400
    try:
        subprocess.run(["python", "export_event_data.py", fmt], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"error": "Export failed"}), 500
    return jsonify({"status": "Data export started"})

@app.route("/user/info", methods=["GET"])
def user_info():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    return jsonify({
        "status": "User information retrieved",
        "user_id": user_id,
        "name": "John Doe",
        "email": "john.doe@example.com"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)