import os
import re
import yaml
import hmac
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

MASTER_PASSWORD = os.getenv('MASTER_PASSWORD')
if MASTER_PASSWORD is None:
    raise RuntimeError("MASTER_PASSWORD environment variable is not set")

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    raw = request.get_data(as_text=True)
    data = yaml.safe_load(raw) or {}
    user_id = data.get('user_id')
    feedback = data.get('feedback')
    return jsonify({
        "status": "Feedback received",
        "user": user_id,
        "feedback": feedback
    })

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_id = request.args.get('id', default='', type=str)
    if not re.fullmatch(r'\w+', report_id):
        return jsonify({"status": "Invalid report id"}), 400
    try:
        subprocess.run(['./report_generator', report_id],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=False)
    except Exception as e:
        return jsonify({"status": "Report generation failed", "error": str(e)}), 500
    return jsonify({"status": "Report generation initiated"})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    entered_password = request.form.get('password', '')
    if hmac.compare_digest(entered_password, MASTER_PASSWORD):
        return jsonify({"status": "Admin login successful"})
    else:
        return jsonify({"status": "Login failed"}), 401

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    raw = request.get_data(as_text=True)
    data = yaml.safe_load(raw) or {}
    return jsonify({
        "status": "Catalog updated",
        "new_catalog": data
    })

if __name__ == '__main__':
    app.run(debug=False)