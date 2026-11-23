import os
import re
import json
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

MASTER_PASSWORD = os.getenv('MASTER_PASSWORD', 'CHANGE_ME')


def json_response(data, status=200):
    return jsonify(data), status


def verify_password(pwd):
    return pwd == MASTER_PASSWORD


def admin_required(func):
    def wrapper(*args, **kwargs):
        payload = request.get_json(silent=True) or {}
        pwd = payload.get('password') or request.form.get('password')
        if not pwd or not verify_password(pwd):
            return json_response({'error': 'Unauthorized'}, 401)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def execute_operation(operation, parameter):
    return {
        'returncode': 0,
        'stdout': f'Executed operation "{operation}" with parameter "{parameter}"',
        'stderr': ''
    }


@app.route('/service/create', methods=['POST'])
def service_create():
    raw_body = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw_body)
    except yaml.YAMLError:
        return json_response({'error': 'Invalid YAML'}, 400)
    if not isinstance(data, dict):
        return json_response({'error': 'YAML must be a dictionary'}, 400)
    return json_response({'message': 'Service created', 'data': data}, 201)


@app.route('/admin/login', methods=['POST'])
def admin_login():
    payload = request.get_json(silent=True) or {}
    pwd = payload.get('password') or request.form.get('password')
    if not pwd:
        return json_response({'error': 'Password required'}, 400)
    if verify_password(pwd):
        return json_response({'message': 'Login successful'})
    return json_response({'error': 'Unauthorized'}, 401)


@app.route('/admin/password', methods=['POST'])
@admin_required
def admin_password():
    payload = request.get_json(silent=True) or {}
    new_pwd = payload.get('new_password') or request.form.get('new_password')
    if not new_pwd:
        return json_response({'error': 'New password required'}, 400)
    global MASTER_PASSWORD
    MASTER_PASSWORD = new_pwd
    return json_response({'message': 'Password updated'})


@app.route('/admin/configure', methods=['POST'])
@admin_required
def admin_configure():
    payload = request.get_json(silent=True) or {}
    config = payload.get('config') or request.form.get('config')
    if not config:
        return json_response({'error': 'Config required'}, 400)
    return json_response({'message': 'Configuration saved'})


@app.route('/operations/start', methods=['POST'])
@admin_required
def operations_start():
    payload = request.get_json(silent=True) or {}
    operation = payload.get('operation')
    parameter = payload.get('parameter')
    if not operation or not parameter:
        return json_response({'error': 'Operation and parameter required'}, 400)
    pattern = r'^[\w-]+$'
    if not re.fullmatch(pattern, operation) or not re.fullmatch(pattern, parameter):
        return json_response({'error': 'Invalid characters in operation or parameter'}, 400)
    result = execute_operation(operation, parameter)
    return json_response({
        'message': 'Operation executed',
        'returncode': result['returncode'],
        'stdout': result['stdout'],
        'stderr': result['stderr']
    })


@app.route('/data/backup', methods=['GET'])
def data_backup():
    fmt = request.args.get('format', '').lower()
    dummy = {'data': [1, 2, 3]}
    if fmt == 'json':
        return json_response(dummy)
    if fmt == 'yaml':
        return json.dumps(dummy), 200, {'Content-Type': 'application/json'}
    if fmt == 'csv':
        csv_data = "value\n1\n2\n3\n"
        return csv_data, 200, {'Content-Type': 'text/csv'}
    return json_response({'error': 'Invalid format'}, 400)


if __name__ == '__main__':
    app.run(debug=False)