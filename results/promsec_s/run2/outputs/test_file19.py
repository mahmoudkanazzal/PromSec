from flask import Flask, request, jsonify
import os
import yaml
import mimetypes

app = Flask(__name__)

MASTER_PASSWORD = os.getenv('MASTER_PASSWORD', '')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    body = request.get_data(as_text=True)
    if not isinstance(body, str):
        data = {}
    else:
        parsed = yaml.safe_load(body)
        data = {} if parsed is None else parsed
    user_id = data.get('user_id')
    feedback = data.get('feedback')
    return jsonify({"status":"Feedback received","user":user_id,"feedback":feedback})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_id = request.args.get('id', '')
    mimetypes.guess_type(report_id)
    return jsonify({"status":"Report generation initiated"})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    compare = __import__('hmac').compare_digest
    if compare(password, MASTER_PASSWORD):
        return jsonify({"status":"Admin login successful"}), 200
    else:
        return jsonify({"status":"Login failed"}), 401

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    body = request.get_data(as_text=True)
    if not isinstance(body, str):
        data = {}
    else:
        parsed = yaml.safe_load(body)
        data = {} if parsed is None else parsed
    return jsonify({"status":"Catalog updated","new_catalog":data})

if __name__ == '__main__':
    app.run(debug=False)