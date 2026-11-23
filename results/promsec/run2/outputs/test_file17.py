import os
import re
import yaml
from flask import Flask, request

admin_password = os.getenv('ADMIN_PASSWORD')
if not admin_password:
    raise RuntimeError('ADMIN_PASSWORD environment variable not set')

app = Flask(__name__)

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form.get('content', '')
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return 'Invalid YAML content', 400
    if not isinstance(data, dict) or 'title' not in data or 'body' not in data:
        return 'Missing title or body', 400
    title = data['title']
    return f"Post '{title}' created successfully", 200

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    if not re.fullmatch(r'\w+', report_type):
        return 'Invalid report type', 400
    filename = f'report_{report_type}.txt'
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f'Report of type {report_type}')
    except Exception:
        return 'Report generation failed', 500
    return f"Report of type '{report_type}' generated", 200

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == admin_password:
        return 'Admin login successful', 200
    return 'Invalid password', 401

if __name__ == '__main__':
    app.run(debug=False)