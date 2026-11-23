import os
import yaml
import subprocess
from flask import Flask, request, abort

app = Flask(__name__)

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
if ADMIN_PASSWORD is None:
    raise RuntimeError("Environment variable ADMIN_PASSWORD must be set for admin authentication")

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form.get('content')
    if not content:
        abort(400, description="Missing 'content' field")
    try:
        data = yaml.safe_load(content)
    except Exception as e:
        abort(400, description=f"Invalid YAML content: {e}")
    if not isinstance(data, dict):
        abort(400, description="YAML content must represent a mapping")
    title = data.get('title')
    body = data.get('body')
    if not isinstance(title, str) or not isinstance(body, str):
        abort(400, description="Both 'title' and 'body' must be strings")
    return f"Post '{title}' created successfully"

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    if not report_type:
        abort(400, description="Missing 'type' query parameter")
    allowed = {'summary', 'detail', 'full'}
    if report_type not in allowed:
        abort(400, description="Invalid report type")
    try:
        subprocess.run(['./generate_report.sh', report_type],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except subprocess.CalledProcessError:
        abort(500, description="Report generation failed")
    return f"Report of type '{report_type}' generated"

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        return "Admin login successful"
    return "Invalid password", 401

if __name__ == '__main__':
    app.run(debug=False)