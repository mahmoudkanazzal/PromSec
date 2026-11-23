import os
import re
import yaml
import hmac
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
MASTER_PASSWORD = os.getenv('MASTER_PASSWORD', 'change_me')

def constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1.encode('utf-8'), val2.encode('utf-8'))

def is_valid_report_id(report_id: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+", report_id))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Missing required fields"}), 400
    user_id = data.get('user_id')
    feedback = data.get('feedback')
    if user_id is None or feedback is None:
        return jsonify({"status": "Missing required fields"}), 400
    return jsonify({"status": "Feedback received", "user": user_id, "feedback": feedback})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_id = request.args.get('id', '')
    if not is_valid_report_id(report_id):
        return jsonify({"status": "Invalid report identifier"}), 400
    try:
        subprocess.run(['./report_generator', report_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        return jsonify({"status": "Failed to start report generation"}), 500
    return jsonify({"status": "Report generation initiated"})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if constant_time_compare(password, MASTER_PASSWORD):
        return jsonify({"status": "Admin login successful"})
    return jsonify({"status": "Login failed"}), 401

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({"status": "Invalid YAML format"}), 400
    return jsonify({"status": "Catalog updated", "new_catalog": data})

if __name__ == '__main__':
    app.run(debug=False)