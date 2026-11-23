from flask import Flask, request
import os
import re
import mimetypes
from yaml import safe_load

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
if ADMIN_PASSWORD is None:
    raise RuntimeError('ADMIN_PASSWORD environment variable not set')

app = Flask(__name__)

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form.get('content', '')
    try:
        data = safe_load(content)
    except Exception:
        return 'Invalid YAML content', 400
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return 'Invalid YAML content', 400
    title = data.get('title')
    body = data.get('body')
    if not title or not body:
        return 'Missing title or body', 400
    return f"Post '{title}' created successfully", 200

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    if not re.fullmatch(r'\w+', report_type):
        return 'Invalid report type', 400
    try:
        mimetypes.guess_type(f"{report_type}.txt")
    except Exception:
        return 'Report generation failed', 500
    return f"Report of type '{report_type}' generated", 200

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == ADMIN_PASSWORD:
        return 'Admin login successful', 200
    return 'Invalid password', 401

if __name__ == '__main__':
    app.run(debug=False)