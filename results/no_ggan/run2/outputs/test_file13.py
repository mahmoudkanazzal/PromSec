from flask import Flask, request, jsonify
import os
import yaml
import re
import subprocess
import threading

app = Flask(__name__)
app.config["ADMIN_SECRET"] = os.getenv("ADMIN_SECRET", "admin_secret_2024")
_secret_lock = threading.Lock()
_VALID_NAME_RE = re.compile(r'^[A-Za-z0-9_-]+$')


@app.route("/config/load", methods=["POST"])
def load_config():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "YAML must be a mapping"}), 400
    config_id = data.get("config_id")
    config_value = data.get("config_value")
    if not config_id or not config_value:
        return jsonify({"status": "Error", "message": "Missing config_id or config_value"}), 400
    return jsonify({"status": "Configuration loaded", "config_id": config_id, "config_value": config_value})


@app.route("/system/start", methods=["GET"])
def system_start():
    module = request.args.get("module")
    param = request.args.get("param")
    if not module or not param:
        return jsonify({"status": "Error", "message": "Missing module or param"}), 400
    if not _VALID_NAME_RE.fullmatch(module) or not _VALID_NAME_RE.fullmatch(param):
        return jsonify({"status": "Error", "message": "Invalid characters in module or param"}), 400
    try:
        subprocess.run(
            ["bash", "start_module.sh", module, param],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return jsonify({"status": "Error", "message": "Failed to start module"}), 500
    return jsonify({"status": "System start initiated"})


@app.route("/auth/validate", methods=["POST"])
def auth_validate():
    secret = request.form.get("secret")
    if secret == app.config["ADMIN_SECRET"]:
        return jsonify({"status": "Validation successful"})
    return jsonify({"status": "Validation failed"}), 401


@app.route("/auth/update_secret", methods=["POST"])
def update_secret():
    current_secret = request.form.get("current_secret")
    new_secret = request.form.get("new_secret")
    if current_secret != app.config["ADMIN_SECRET"]:
        return jsonify({"status": "Error", "message": "Unauthorized"}), 401
    if not new_secret:
        return jsonify({"status": "Error", "message": "New secret cannot be empty"}), 400
    with _secret_lock:
        app.config["ADMIN_SECRET"] = new_secret
    return jsonify({"status": "Secret updated"})


@app.route("/config/retrieve", methods=["GET"])
def retrieve_config():
    config_id = request.args.get("config_id")
    if not config_id:
        return jsonify({"status": "Error", "message": "Missing config_id"}), 400
    return jsonify(
        {
            "status": "Configuration retrieved",
            "config": {"config_id": config_id, "config_value": "Sample Config Value"},
        }
    )


@app.route("/config/remove", methods=["POST"])
def remove_config():
    config_id = request.form.get("config_id")
    if not config_id:
        return jsonify({"status": "Error", "message": "Missing config_id"}), 400
    return jsonify({"status": "Configuration removed", "config_id": config_id})


@app.route("/system/status", methods=["GET"])
def system_status():
    module_id = request.args.get("module_id")
    if not module_id:
        return jsonify({"status": "Error", "message": "Missing module_id"}), 400
    return jsonify(
        {"status": "System status", "module_id": module_id, "status_detail": "Active"}
    )


@app.route("/auth/configure", methods=["POST"])
def auth_configure():
    secret = request.form.get("secret")
    setting = request.form.get("setting")
    if secret != app.config["ADMIN_SECRET"]:
        return jsonify({"status": "Error", "message": "Unauthorized"}), 401
    if not setting:
        return jsonify({"status": "Error", "message": "Missing setting"}), 400
    return jsonify({"status": "Setting configured", "setting": setting})


@app.route("/system/logs", methods=["GET"])
def system_logs():
    module_id = request.args.get("module_id")
    if not module_id:
        return jsonify({"status": "Error", "message": "Missing module_id"}), 400
    logs = f"Logs for module {module_id}"
    return jsonify({"status": "System logs", "module_id": module_id, "logs": logs})


@app.route("/data/backup", methods=["GET"])
def data_backup():
    backup_type = request.args.get("type", "json")
    if backup_type not in ("json", "sql"):
        return jsonify({"status": "Error", "message": "Invalid backup type"}), 400
    try:
        subprocess.run(
            ["python", "backup_data.py", backup_type],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return jsonify({"status": "Error", "message": "Backup failed"}), 500
    return jsonify({"status": "Data backup started"})


@app.route("/user/profile", methods=["GET"])
def user_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"status": "Error", "message": "Missing user_id"}), 400
    profile = {
        "user_id": user_id,
        "name": "Emily Davis",
        "email": "emily.davis@example.com",
    }
    return jsonify({"status": "User profile retrieved", "profile": profile})


if __name__ == "__main__":
    app.run(debug=False)