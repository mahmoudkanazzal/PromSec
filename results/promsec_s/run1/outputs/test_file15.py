import os
import re
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'default_change_me')


def _validate_alphanumeric(value, allow_empty=False):
    """
    Validate that the given string contains only letters, digits, underscore, or hyphen.
    Raises ValueError if validation fails.
    """
    if allow_empty and value == '':
        return
    if not isinstance(value, str):
        raise ValueError('Value must be a string')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Invalid characters detected')


def validate_yaml(yaml_str):
    """
    Parse YAML safely and return the resulting object.
    Returns None on parsing errors.
    """
    try:
        data = yaml.safe_load(yaml_str)
        return data
    except yaml.YAMLError:
        return None


def run_service(service, param):
    """
    Placeholder for service execution logic.
    Validates inputs; real implementation would start the service.
    """
    _validate_alphanumeric(service, allow_empty=True)
    _validate_alphanumeric(param, allow_empty=True)
    # Real service execution logic would be added here.


def backup_data_func(backup_format):
    """
    Placeholder for data backup logic.
    Validates the format; real implementation would initiate backup.
    """
    _validate_alphanumeric(backup_format)
    # Real backup logic would be added here.


@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw_body = request.get_data(as_text=True, decode_unicode=True, errors='replace')
    data = validate_yaml(raw_body)
    if not isinstance(data, dict) or 'config_name' not in data or 'config_value' not in data:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML data'}), 400
    config_name = data['config_name']
    config_value = data['config_value']
    try:
        _validate_alphanumeric(str(config_name))
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({
        'status': 'Configuration uploaded',
        'config_name': config_name,
        'config_value': config_value
    }), 200


@app.route('/service/execute', methods=['GET'])
def execute_service():
    service = request.args.get('service', '')
    param = request.args.get('param', '')
    try:
        run_service(service, param)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({'status': 'Service execution started'}), 200


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == ADMIN_PASSWORD:
        return jsonify({'status': 'Login successful'}), 200
    return jsonify({'status': 'Login failed'}), 401


@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    global ADMIN_PASSWORD
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    if current_password != ADMIN_PASSWORD:
        return jsonify({'status': 'Access denied'}), 401
    if not new_password:
        return jsonify({'status': 'Error', 'message': 'New password is required'}), 400
    ADMIN_PASSWORD = new_password
    return jsonify({'status': 'Password updated'}), 200


@app.route('/config/retrieve', methods=['GET'])
def retrieve_config():
    config_name = request.args.get('config_name')
    if not config_name:
        return jsonify({'status': 'Error', 'message': 'Configuration name is required'}), 400
    try:
        _validate_alphanumeric(config_name)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({
        'status': 'Configuration retrieved',
        'config': {
            'config_name': config_name,
            'config_value': 'Sample Config Value'
        }
    }), 200


@app.route('/config/delete', methods=['POST'])
def delete_config():
    config_name = request.form.get('config_name')
    if not config_name:
        return jsonify({'status': 'Error', 'message': 'Configuration name is required'}), 400
    try:
        _validate_alphanumeric(config_name)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({'status': 'Configuration deleted', 'config_name': config_name}), 200


@app.route('/service/status', methods=['GET'])
def service_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Job ID is required'}), 400
    try:
        _validate_alphanumeric(job_id)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({
        'status': 'Service status',
        'job_id': job_id,
        'status_detail': 'Running'
    }), 200


@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    password = request.form.get('password', '')
    setting = request.form.get('setting')
    if password != ADMIN_PASSWORD:
        return jsonify({'status': 'Access denied'}), 401
    if not setting:
        return jsonify({'status': 'Error', 'message': 'Setting is required'}), 400
    try:
        _validate_alphanumeric(setting)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting}), 200


@app.route('/service/logs', methods=['GET'])
def service_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Job ID is required'}), 400
    try:
        _validate_alphanumeric(job_id)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({
        'status': 'Service logs',
        'job_id': job_id,
        'logs': f'Sample logs for job {job_id}'
    }), 200


@app.route('/backup/data', methods=['GET'])
def backup_data():
    backup_format = request.args.get('format', 'json')
    try:
        backup_data_func(backup_format)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
    return jsonify({'status': 'Data backup started'}), 200


@app.route('/user/info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'User ID is required'}), 400
    try:
        _validate_alphanumeric(user_id)
    except ValueError as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 400
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