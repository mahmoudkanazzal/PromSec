import os
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

CURRENT_SECRET = os.getenv('SECRET_KEY', 'change_me_to_a_secure_value')


class ConfigManager:
    @staticmethod
    def load_config(yaml_data):
        try:
            return yaml.safe_load(yaml_data)
        except yaml.YAMLError:
            return None

    @staticmethod
    def validate_config(config):
        return isinstance(config, dict) and 'config_name' in config and 'config_value' in config


class AdminManager:
    @staticmethod
    def check_secret(secret):
        return secret == CURRENT_SECRET

    @staticmethod
    def update_secret(new_secret):
        global CURRENT_SECRET
        CURRENT_SECRET = new_secret


@app.route('/config/upload', methods=['POST'])
def upload_config():
    raw = request.get_data(as_text=True)
    config = ConfigManager.load_config(raw)
    if config is None:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML'}), 400
    if not ConfigManager.validate_config(config):
        return jsonify({'status': 'Error', 'message': 'Invalid configuration format'}), 400
    return jsonify({
        'status': 'Configuration uploaded',
        'config_name': config['config_name'],
        'config_value': config['config_value']
    })


@app.route('/system/execute', methods=['GET'])
def system_execute():
    command = request.args.get('command')
    param = request.args.get('param')
    allowed = {'start', 'stop', 'restart'}
    if command not in allowed:
        return jsonify({'status': 'Error', 'message': 'Command not allowed'}), 400
    return jsonify({'status': 'System execution started'})


@app.route('/admin/verify', methods=['POST'])
def admin_verify():
    secret = request.form.get('secret', '')
    if AdminManager.check_secret(secret):
        return jsonify({'status': 'Verification successful'})
    return jsonify({'status': 'Verification failed'}), 401


@app.route('/admin/change_secret', methods=['POST'])
def change_secret():
    current = request.form.get('current_secret', '')
    new = request.form.get('new_secret', '')
    if not AdminManager.check_secret(current) or not new:
        return jsonify({'status': 'Verification failed'}), 401
    AdminManager.update_secret(new)
    return jsonify({'status': 'Secret changed successfully'})


@app.route('/config/get', methods=['GET'])
def get_config():
    name = request.args.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'Missing config_name'}), 400
    return jsonify({
        'status': 'Configuration retrieved',
        'config': {'config_name': name, 'config_value': 'Example Value'}
    })


@app.route('/config/delete', methods=['POST'])
def delete_config():
    name = request.form.get('config_name')
    if not name:
        return jsonify({'status': 'Error', 'message': 'Missing config_name'}), 400
    return jsonify({'status': 'Configuration deleted', 'config_name': name})


@app.route('/system/status', methods=['GET'])
def system_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Missing job_id'}), 400
    return jsonify({
        'status': 'System status',
        'job_id': job_id,
        'state': 'Running'
    })


@app.route('/admin/settings', methods=['POST'])
def admin_settings():
    secret = request.form.get('secret', '')
    if not AdminManager.check_secret(secret):
        return jsonify({'status': 'Access denied'}), 401
    setting = request.form.get('setting')
    if not setting:
        return jsonify({'status': 'Error', 'message': 'Missing setting'}), 400
    return jsonify({'status': 'Setting updated', 'setting': setting})


@app.route('/system/logs', methods=['GET'])
def system_logs():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'status': 'Error', 'message': 'Missing job_id'}), 400
    return jsonify({
        'status': 'System logs',
        'job_id': job_id,
        'logs': f'Sample logs for job {job_id}'
    })


@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', 'json')
    allowed = {'json', 'yaml', 'csv'}
    if fmt not in allowed:
        return jsonify({'status': 'Error', 'message': 'Invalid format'}), 400
    return jsonify({'status': 'Data backup started'})


@app.route('/user/details', methods=['GET'])
def user_details():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'Error', 'message': 'Missing user_id'}), 400
    return jsonify({
        'status': 'User details retrieved',
        'user': {
            'user_id': user_id,
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com'
        }
    })


if __name__ == '__main__':
    app.run(debug=False)