from flask import Flask, request, jsonify
import os
import yaml
import re

MASTER_PASSWORD = os.getenv('MASTER_PASSWORD')
if not MASTER_PASSWORD:
    raise RuntimeError('MASTER_PASSWORD environment variable not set')

app = Flask(__name__)

def _create_report_file(report_id: str) -> str:
    reports_dir = os.path.join(os.getcwd(), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, f'{report_id}.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f'Report generated for ID: {report_id}')
    return file_path

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    raw = request.get_data(as_text=True)
    data = yaml.safe_load(raw) or {}
    user_id = data.get('user_id')
    feedback = data.get('feedback')
    return jsonify({'status': 'Feedback received', 'user': user_id, 'feedback': feedback})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_id = request.args.get('id', '')
    if not re.fullmatch(r'^[A-Za-z0-9_-]+$', report_id):
        return jsonify({'status': 'Invalid report id'}), 400
    _create_report_file(report_id)
    return jsonify({'status': 'Report generation initiated'})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == MASTER_PASSWORD:
        return jsonify({'status': 'Admin login successful'})
    return jsonify({'status': 'Login failed'}), 401

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    raw = request.get_data(as_text=True)
    catalog = yaml.safe_load(raw)
    return jsonify({'status': 'Catalog updated', 'new_catalog': catalog})

if __name__ == '__main__':
    app.run(debug=False)