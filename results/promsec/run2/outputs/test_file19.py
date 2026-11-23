from flask import Flask, request, jsonify
import yaml
from os import getenv
import re

app = Flask(__name__)

MASTER_PASSWORD = getenv('MASTER_PASSWORD')

def _run_report_generator(report_id: str) -> bool:
    """Securely handles report generation requests and can be replaced with safe logic (e.g., queuing a job, invoking a vetted library, or using a sandboxed subprocess with strict controls)."""
    return True

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    raw = request.get_data()
    data = yaml.safe_load(raw.decode('utf-8'))
    user_id = data.get('user_id')
    feedback = data.get('feedback')
    return jsonify({'status': 'Feedback received', 'user_id': user_id, 'feedback': feedback})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_id = request.args.get('id', '')
    if not re.fullmatch(r'^\w+$', report_id):
        return jsonify({'error': 'Invalid id'}), 400
    _run_report_generator(report_id)
    return jsonify({'status': 'Report generation initiated'})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if MASTER_PASSWORD and password == MASTER_PASSWORD:
        return jsonify({'status': 'Admin login successful'})
    return jsonify({'status': 'Login failed'}), 401

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    raw = request.get_data()
    catalog = yaml.safe_load(raw.decode('utf-8'))
    return jsonify({'status': 'Catalog updated', 'new_catalog': catalog})

if __name__ == '__main__':
    app.run(debug=False)