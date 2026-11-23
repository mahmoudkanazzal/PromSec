from flask import Flask, request, jsonify
import os
import yaml
import subprocess

app = Flask(__name__)

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Invalid YAML format"}), 400
    if not isinstance(data, dict) or not all(k in data for k in ('station_id', 'temperature', 'humidity')):
        return jsonify({"status": "Missing required reading fields"}), 400
    station_id = data['station_id']
    return jsonify({"status": "Readings uploaded", "station": station_id}), 200

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '').strip()
    if report_type not in ('summary', 'detailed', 'hourly'):
        return jsonify({"status": "Invalid report type"}), 400
    try:
        subprocess.run(['./weather_report_tool', report_type], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return jsonify({"status": "Failed to start report generation"}), 500
    return jsonify({"status": "Report generation started"}), 200

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if token == STATION_ACCESS_TOKEN:
        return jsonify({"status": "Station authenticated"}), 200
    return jsonify({"status": "Authentication failed"}), 401

if __name__ == '__main__':
    app.run(debug=False)