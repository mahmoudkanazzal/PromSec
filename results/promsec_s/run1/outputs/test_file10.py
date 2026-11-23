import os
import re
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

ADMIN_PASSWORD = {"value": os.getenv("ADMIN_PASSWORD", "event_admin_2024")}

def _is_safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+", value))

def _is_allowed_format(fmt: str) -> bool:
    return fmt in {"json", "csv", "xml"}

@app.route("/event/add", methods=["POST"])
def add_event():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    event_id = data.get("event_id")
    event_name = data.get("event_name")
    event_date = data.get("event_date")
    if not event_id or not event_name or not event_date:
        return jsonify({"status": "Error", "message": "Missing event information"}), 400
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
    if not _is_safe_identifier(event_id) or not _is_safe_identifier(task):
        return jsonify({"status": "Error", "message": "Invalid parameters"}), 400
    return jsonify({"status": "Event started"})

@app.route("/auth/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    if password == ADMIN_PASSWORD["value"]:
        return jsonify({"status": "Login successful"})
    return jsonify({"status": "Login failed"}), 401

@app.route("/auth/update_password", methods=["POST"])
def update_password():
    password = request.form.get("password", "")
    new_password = request.form.get("new_password", "")
    if password != ADMIN_PASSWORD["value"]:
        return jsonify({"status": "Login failed"}), 401
    if not new_password:
        return jsonify({"status": "Error", "message": "Invalid new password"}), 400
    ADMIN_PASSWORD["value"] = new_password
    return jsonify({"status": "Password updated"})

@app.route("/event/get", methods=["GET"])
def get_event():
    event_id = request.args.get("event_id")
    if not event_id:
        return jsonify({"status": "Error", "message": "Event ID is required"}), 400
    return jsonify({
        "status": "Event retrieved",
        "event": {
            "event_id": event_id,
            "event_name": "Sample Event",
            "event_date": "2024-01-01"
        }
    })

@app.route("/event/remove", methods=["POST"])
def remove_event():
    event_id = request.form.get("event_id")
    if not event_id:
        return jsonify({"status": "Error", "message": "Event ID is required"}), 400
    return jsonify({"status": "Event removed", "event_id": event_id})

@app.route("/task/status", methods=["GET"])
def task_status():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task status", "task_id": task_id, "status": "In Progress"})

@app.route("/auth/settings", methods=["POST"])
def auth_settings():
    password = request.form.get("password", "")
    setting = request.form.get("setting", "")
    if password != ADMIN_PASSWORD["value"]:
        return jsonify({"status": "Access denied"}), 401
    if not setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400
    return jsonify({"status": "Setting updated", "setting": setting})

@app.route("/task/logs", methods=["GET"])
def task_logs():
    task_id = request.args.get("task_id")
    if not task_id:
        return jsonify({"status": "Error", "message": "Task ID is required"}), 400
    return jsonify({"status": "Task logs", "task_id": task_id, "logs": f"Logs for task {task_id}"})

@app.route("/data/export", methods=["GET"])
def data_export():
    fmt = request.args.get("format", "json")
    if not _is_allowed_format(fmt):
        return jsonify({"status": "Error", "message": "Unsupported export format"}), 400
    return jsonify({"status": "Data export started"})

@app.route("/user/info", methods=["GET"])
def user_info():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"status": "Error", "message": "User ID is required"}), 400
    return jsonify({
        "status": "User information retrieved",
        "user_info": {
            "user_id": user_id,
            "name": "John Doe",
            "email": "john.doe@example.com"
        }
    })

if __name__ == "__main__":
    app.run(debug=False)