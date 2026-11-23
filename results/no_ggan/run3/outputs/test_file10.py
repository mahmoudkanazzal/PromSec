import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

_initial_password = os.getenv('ADMIN_PASSWORD') or "ChangeMeNow!"
admin_password_hash = generate_password_hash(_initial_password)


def verify_admin_password(password: str) -> bool:
    return check_password_hash(admin_password_hash, password)


def set_admin_password(new_password: str):
    global admin_password_hash
    admin_password_hash = generate_password_hash(new_password)


def is_safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))


def is_safe_format(fmt: str) -> bool:
    return fmt.lower() in {"json", "csv", "xml"}


@app.route('/event/add', methods=['POST'])
def event_add():
    try:
        raw = request.data.decode('utf-8')
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify(error="Invalid YAML"), 400
    if not isinstance(data, dict):
        return jsonify(error="YAML must be a mapping"), 400
    required = ['event_id', 'event_name', 'event_date']
    for key in required:
        if not data.get(key):
            return jsonify(error=f"Missing or empty field: {key}"), 400
    return jsonify(status="Event added",
                   event_id=data['event_id'],
                   event_name=data['event_name'],
                   event_date=data['event_date'])


@app.route('/event/start', methods=['GET'])
def event_start():
    event_id = request.args.get('event_id', '')
    task = request.args.get('task', '')
    if not (is_safe_identifier(event_id) and is_safe_identifier(task)):
        return jsonify(error="Invalid parameters"), 400
    try:
        subprocess.run(["sh", "start_event.sh", event_id, task],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify(error="Failed to start event"), 500
    return jsonify(status="Event started")


@app.route('/auth/login', methods=['POST'])
def auth_login():
    password = request.form.get('password', '')
    if verify_admin_password(password):
        return jsonify(status="Login successful")
    return jsonify(status="Login failed"), 401


@app.route('/auth/update_password', methods=['POST'])
def auth_update_password():
    password = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if not verify_admin_password(password):
        return jsonify(status="Login failed"), 401
    if not new_password:
        return jsonify(error="New password cannot be empty"), 400
    set_admin_password(new_password)
    return jsonify(status="Password updated")


@app.route('/event/get', methods=['GET'])
def event_get():
    event_id = request.args.get('event_id')
    if not event_id:
        return jsonify(error="Missing event_id"), 400
    return jsonify(status="Event retrieved",
                   event=dict(event_id=event_id,
                              event_name="Sample Event",
                              event_date="2024-01-01"))


@app.route('/event/remove', methods=['POST'])
def event_remove():
    event_id = request.form.get('event_id')
    if not event_id:
        return jsonify(error="Missing event_id"), 400
    return jsonify(status="Event removed", event_id=event_id)


@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify(error="Missing task_id"), 400
    return jsonify(status="Task status",
                   task_id=task_id,
                   status_detail="In Progress")


@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password', '')
    setting = request.form.get('setting', '')
    if not verify_admin_password(password):
        return jsonify(status="Access denied"), 401
    if not setting:
        return jsonify(error="Setting cannot be empty"), 400
    return jsonify(status="Setting updated", setting=setting)


@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify(error="Missing task_id"), 400
    return jsonify(status="Task logs",
                   task_id=task_id,
                   logs=f"Logs for task {task_id}")


@app.route('/data/export', methods=['GET'])
def data_export():
    fmt = request.args.get('format', 'json')
    if not is_safe_format(fmt):
        return jsonify(error="Invalid format"), 400
    try:
        subprocess.run(["python", "export_event_data.py", fmt],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify(error="Data export failed"), 500
    return jsonify(status="Data export started")


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(error="Missing user_id"), 400
    return jsonify(status="User information retrieved",
                   user=dict(user_id=user_id,
                             name="John Doe",
                             email="john.doe@example.com"))


if __name__ == "__main__":
    app.run(debug=False)