import os
import re
import yaml
import subprocess
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

MASTER_PASSWORD = os.getenv('MASTER_PASSWORD')
if not MASTER_PASSWORD:
    logging.error('MASTER_PASSWORD environment variable is not set')
    raise RuntimeError('Missing MASTER_PASSWORD environment variable')

REPORT_ID_PATTERN = re.compile(r'^\w+$')


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        raw_data = request.get_data(as_text=True)
        data = yaml.safe_load(raw_data) or {}
        user_id = data.get('user_id')
        feedback = data.get('feedback')
        if not user_id or not feedback:
            return jsonify({"status": "Invalid feedback data"}), 400
        return jsonify({"status": "Feedback received", "user": user_id, "feedback": feedback})
    except Exception:
        logging.exception('Error processing feedback')
        return jsonify({"status": "Error processing feedback"}), 500


@app.route('/generate_report', methods=['GET'])
def generate_report():
    try:
        report_id = request.args.get('id', '')
        if not REPORT_ID_PATTERN.fullmatch(report_id):
            return jsonify({"status": "Invalid report identifier"}), 400
        subprocess.run(['./report_generator', report_id], check=False)
        return jsonify({"status": "Report generation initiated"})
    except Exception:
        logging.exception('Error initiating report generation')
        return jsonify({"status": "Error initiating report generation"}), 500


@app.route('/admin_login', methods=['POST'])
def admin_login():
    entered_password = request.form.get('password', '')
    if entered_password == MASTER_PASSWORD:
        return jsonify({"status": "Admin login successful"})
    else:
        return jsonify({"status": "Login failed"}), 401


@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    try:
        raw_data = request.get_data(as_text=True)
        catalog_data = yaml.safe_load(raw_data) or {}
        return jsonify({"status": "Catalog updated", "new_catalog": catalog_data})
    except Exception:
        logging.exception('Error updating catalog')
        return jsonify({"status": "Error updating catalog"}), 500


if __name__ == '__main__':
    app.run(debug=False)