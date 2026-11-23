from flask import Flask, request, abort, jsonify
import os
import yaml
import subprocess

admin_password = os.getenv('ADMIN_PASSWORD')
if not admin_password:
    raise RuntimeError("Environment variable ADMIN_PASSWORD must be set for admin authentication")

app = Flask(__name__)

@app.route('/create_post', methods=['POST'])
def create_post():
    content = request.form.get('content')
    if not content:
        return jsonify({"error": "Missing 'content' parameter"}), 400
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return jsonify({"error": f"Invalid YAML format: {e}"}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "YAML content must represent a mapping"}), 400
    title = data.get('title')
    body = data.get('body')
    if not isinstance(title, str) or not isinstance(body, str):
        return jsonify({"error": "Both 'title' and 'body' must be strings"}), 400
    return jsonify({"message": f"Post '{title}' created successfully"}), 201

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    if report_type not in ('summary', 'detail'):
        return jsonify({"error": "Invalid report type"}), 400
    try:
        subprocess.run(['./generate_report.sh', report_type], check=True)
    except FileNotFoundError:
        return jsonify({"error": "Report generation script not found"}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Report generation failed: {e}"}), 500
    return jsonify({"message": f"Report of type '{report_type}' generated"}), 200

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == admin_password:
        return jsonify({"message": "Admin login successful"}), 200
    else:
        return jsonify({"error": "Invalid password"}), 401

if __name__ == '__main__':
    app.run(debug=False)