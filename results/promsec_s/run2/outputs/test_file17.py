from flask import Flask, request
import os
from yaml import safe_load
import hmac
import mimetypes

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

app = Flask(__name__)

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form.get('content')
    if content is None:
        return 'Invalid YAML', 400
    try:
        data = safe_load(content)
    except Exception:
        return 'Invalid YAML', 400
    if not isinstance(data, dict):
        return 'Invalid YAML', 400
    title = data.get('title')
    body = data.get('body')
    if not title or not body:
        return 'Invalid YAML', 400
    return f"Post '{title}' created successfully", 200

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    mime_type, _ = mimetypes.guess_type(f"{report_type}.txt")
    if mime_type is None:
        mime_type = 'application/octet-stream'
    return f"Report type: {report_type}, MIME: {mime_type}", 200

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password is None:
        return 'Invalid password', 401
    if hmac.compare_digest(password, ADMIN_PASSWORD):
        return 'Admin login successful', 200
    return 'Invalid password', 401

if __name__ == '__main__':
    app.run(debug=False)