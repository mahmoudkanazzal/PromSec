import os
import subprocess
import yaml
from flask import Flask, request, jsonify

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')
ALLOWED_REPORT_TYPES = {"summary", "detailed", "hourly", "daily"}

app = Flask(__name__)

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    try:
        raw_data = request.get_data()
        text = raw_data.decode('utf-8')
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError('Invalid payload format')
        required_keys = {'station_id', 'temperature', 'humidity'}
        if not required_keys.issubset(data.keys()):
            return jsonify({"status": "Missing required fields"}), 400
        station_id = data['station_id']
        return jsonify({"status": "Readings uploaded", "station": station_id}), 200
    except Exception as e:
        return jsonify({"status": "Invalid YAML payload", "error": str(e)}), 400

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '').lower()
    if report_type not in ALLOWED_REPORT_TYPES:
        return jsonify({"status": "Invalid report type"}), 400
    try:
        subprocess.run(
            ["./weather_report_tool", report_type],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({"status": "Report generation started"}), 200
    except Exception as e:
        return jsonify({"status": "Failed to start report generation", "error": str(e)}), 500

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if token == STATION_ACCESS_TOKEN:
        return jsonify({"status": "Station authenticated"}), 200
    else:
        return jsonify({"status": "Authentication failed"}), 401

if __name__ == '__main__':
    app.run(debug=False)