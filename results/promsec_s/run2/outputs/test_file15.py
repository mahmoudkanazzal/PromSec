from flask import Flask, request, jsonify
import yaml
import os
import re
import mimetypes

app = Flask(__name__)

admin_password = os.getenv('ADMIN_PASSWORD', 'default_change_me')
allowed_pattern = re.compile(r'^[\w\-]+$')


def validate_yaml(data):
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError:
        return None


@app.route('/config/upload', methods=['POST'])
def config_upload():
    raw = request.get_data(as_text=True)
    parsed = validate_yaml(raw)
    if not isinstance(parsed, dict) or 'config_name' not in parsed or 'config_value' not in parsed:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML data'}), 400
    return jsonify({
        'status': 'Configuration uploaded',
        'config_name': parsed['config_name'],
        'config_value': parsed['config_value']
    }), 200


@app.route('/service/execute', methods=['GET'])
def service_execute():
    service = request.args.get('service')
    param = request.args.get('param')
    if not service or not param or not allowed_pattern.match(service) or not allowed_pattern.match(param):
        return jsonify({'status': 'Error', 'message': 'Invalid parameters'}), 400
    return jsonify({'status': 'Service execution started'}), 200


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == admin_password:
        return jsonify({'status': 'Login successful'}), 200
    return jsonify({'status': 'Login failed'}), 401


@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global admin_password
    current = request.form.get('current_password')
    new = request.form.get('new_password')
    if current != admin_password:
        return jsonify({'status': 'Access denied'}), 401
    if not new:
        return jsonify({'status': 'Error', 'message': 'New password cannot be empty'}), 400
    admin_password = new
    return jsonify({'status': 'Password updated'}), 200


@app.route('/config/retrieve', methods=['GET'])
def config_retrieve():
    name = request.args.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'Missing config_name'}), 400
    return jsonify({
        'status': 'Configuration retrieved',
        'config': {'config_name': name, 'config_value': 'Sample Config Value'}
    }), 200


@app.route('/config/delete', methods=['POST'])
def config_delete():
    name = request.form.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'Missing config_name'}), 400
    return jsonify({'status': 'Configuration deleted', 'config_name': name}), 200


@app.route('/service/status', methods=['GET'])
def service_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Missing job_id'}), 400
    return jsonify({'status': 'Service status', 'job_id': job_id, 'status': 'Running'}), 200


@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password')
    setting = request.form.get('setting')
    if password != admin_password:
        return jsonify({'status': 'Access denied'}), 401
    if not setting:
        return jsonify({'status': 'Error', 'message': 'Setting cannot be empty'}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting}), 200


@app.route('/service/logs', methods=['GET'])
def service_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Missing job_id'}), 400
    return jsonify({
        'status': 'Service logs',
        'job_id': job_id,
        'logs': f'Sample logs for job {job_id}'
    }), 200


@app.route('/backup/data', methods=['GET'])
def backup_data():
    fmt = request.args.get('format', 'json')
    if fmt not in ('json', 'yaml', 'csv'):
        return jsonify({'status': 'Error', 'message': 'Invalid format'}), 400
    mimetypes.guess_type(f'backup.{fmt}')
    return jsonify({'status': 'Data backup started'}), 200


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'Missing user_id'}), 400
    return jsonify({
        'status': 'User information retrieved',
        'user': {
            'user_id': user_id,
            'name': 'Samuel Green',
            'email': 'samuel.green@example.com'
        }
    }), 200


if __name__ == '__main__':
    app.run(debug=False)