import os
import yaml
import mimetypes
from flask import Flask, request, jsonify

master_password = os.getenv('MASTER_PASSWORD')
if not master_password:
    raise RuntimeError('MASTER_PASSWORD environment variable not set')

app = Flask(__name__)

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
    mimetypes.guess_type(report_id)
    return jsonify({'status': 'Report generation initiated'})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == master_password:
        return jsonify({'status': 'Admin login successful'}), 200
    else:
        return jsonify({'status': 'Login failed'}), 401

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    raw = request.get_data(as_text=True)
    catalog = yaml.safe_load(raw)
    return jsonify({'status': 'Catalog updated', 'new_catalog': catalog})

if __name__ == '__main__':
    app.run(debug=False)