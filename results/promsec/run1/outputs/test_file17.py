from flask import Flask, request, abort
import os
import yaml
import hmac

admin_password = os.getenv('ADMIN_PASSWORD')
if not admin_password:
    raise RuntimeError("ADMIN_PASSWORD environment variable not set")

app = Flask(__name__)

def _generate_report_content(report_type):
    if report_type == "summary":
        return "Summary report content"
    if report_type == "detail":
        return "Detail report content"
    if report_type == "full":
        return "Full report content"
    raise ValueError("Unsupported report type")

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form.get('content', '')
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        abort(400, description="Invalid YAML content")
    if data is None:
        data = {}
    if not isinstance(data, dict):
        abort(400, description="Invalid YAML content")
    title = data.get('title')
    body = data.get('body')
    if not title or not body:
        abort(400, description="Missing title or body in post data")
    return f"Post '{title}' created successfully"

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    if report_type not in ("summary", "detail", "full"):
        abort(400, description="Invalid report type")
    try:
        _generate_report_content(report_type)
    except Exception:
        abort(500, description="Report generation failed")
    return f"Report of type '{report_type}' generated"

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, admin_password):
        return "Admin login successful"
    return "Invalid password", 401

if __name__ == '__main__':
    app.run(debug=False)