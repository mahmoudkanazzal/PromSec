import os
import re
import yaml
import logging
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_password = os.getenv('ADMIN_PASSWORD', 'change_me')
password_hash = generate_password_hash(admin_password)

def is_safe_identifier(value):
    return re.fullmatch(r'^[A-Za-z0-9_-]+$', value) is not None

def _run_start_event(event_id, task):
    logger.info(f'Starting event {event_id} with task {task}')
    try:
        return True
    except Exception as e:
        logger.error(f'Error starting event: {e}')
        return False

def _export_event_data(export_format):
    logger.info(f'Exporting data in format {export_format}')
    try:
        return True
    except Exception as e:
        logger.error(f'Error exporting data: {e}')
        return False

@app.route('/event/add', methods=['POST'])
def add_event():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError
        event_id = data.get('event_id')
        event_name = data.get('event_name')
        event_date = data.get('event_date')
        if not all([event_id, event_name, event_date]):
            raise ValueError
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    return jsonify({'status': 'Event added', 'event_id': event_id, 'event_name': event_name, 'event_date': event_date})

@app.route('/event/start', methods=['GET'])
def start_event():
    event_id = request.args.get('event_id', '')
    task = request.args.get('task', '')
    if not (is_safe_identifier(event_id) and is_safe_identifier(task)):
        return jsonify({'status': 'Error', 'message': 'Invalid parameters'}), 400
    if not _run_start_event(event_id, task):
        return jsonify({'status': 'Error', 'message': 'Failed to start event'}), 500
    return jsonify({'status': 'Event started'})

@app.route('/auth/login', methods=['POST'])
def login():
    password = request.form.get('password', '')
    if check_password_hash(password_hash, password):
        return jsonify({'status': 'Login successful'})
    return jsonify({'status': 'Login failed'}), 401

@app.route('/auth/update_password', methods=['POST'])
def update_password():
    global password_hash
    current = request.form.get('password', '')
    new_password = request.form.get('new_password', '')
    if not check_password_hash(password_hash, current):
        return jsonify({'status': 'Login failed'}), 401
    if not new_password:
        return jsonify({'status': 'Error', 'message': 'Invalid new password'}), 400
    password_hash = generate_password_hash(new_password)
    return jsonify({'status': 'Password updated'})

@app.route('/event/get', methods=['GET'])
def get_event():
    event_id = request.args.get('event_id')
    if not event_id:
        return jsonify({'status': 'Error', 'message': 'Event ID is required'}), 400
    return jsonify({'event_id': event_id, 'event_name': 'Sample Event', 'event_date': '2024-01-01'})

@app.route('/event/remove', methods=['POST'])
def remove_event():
    event_id = request.form.get('event_id')
    if not event_id:
        return jsonify({'status': 'Error', 'message': 'Event ID is required'}), 400
    return jsonify({'status': 'Event removed', 'event_id': event_id})

@app.route('/task/status', methods=['GET'])
def task_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'status': 'Error', 'message': 'Task ID is required'}), 400
    return jsonify({'status': 'Task status', 'task_id': task_id, 'status': 'In Progress'})

@app.route('/auth/settings', methods=['POST'])
def auth_settings():
    password = request.form.get('password', '')
    setting = request.form.get('setting', '')
    if not check_password_hash(password_hash, password):
        return jsonify({'status': 'Access denied'}), 401
    if not setting:
        return jsonify({'status': 'Error', 'message': 'Invalid setting'}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting})

@app.route('/task/logs', methods=['GET'])
def task_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'status': 'Error', 'message': 'Task ID is required'}), 400
    return jsonify({'status': 'Task logs', 'task_id': task_id, 'logs': f'Logs for task {task_id}'})

@app.route('/data/export', methods=['GET'])
def data_export():
    export_format = request.args.get('format', 'json')
    if export_format not in ('json', 'csv'):
        return jsonify({'status': 'Error', 'message': 'Unsupported export format'}), 400
    if not _export_event_data(export_format):
        return jsonify({'status': 'Error', 'message': 'Failed to start data export'}), 500
    return jsonify({'status': 'Data export started'})

@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'User ID is required'}), 400
    return jsonify({'user_id': user_id, 'name': 'John Doe', 'email': 'john.doe@example.com'})

if __name__ == '__main__':
    app.run(debug=False)