from flask import Flask, request, jsonify
import os
import subprocess
import yaml

token = os.getenv('STATION_ACCESS_TOKEN')
if not token:
    raise RuntimeError("Environment variable STATION_ACCESS_TOKEN is not set")

app = Flask(__name__)

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.get_data(as_text=True)
    data = yaml.safe_load(raw) or {}
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    return jsonify({"status": "Readings uploaded", "station": station_id})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    if report_type not in ('summary', 'detailed'):
        return jsonify({"status": "Invalid report type"}), 400
    subprocess.run(['./weather_report_tool', report_type], check=False)
    return jsonify({"status": "Report generation started"})

@app.route('/station_login', methods=['POST'])
def station_login():
    provided = request.form.get('token', '')
    if provided == token:
        return jsonify({"status": "Station authenticated"})
    return jsonify({"status": "Authentication failed"}), 401

if __name__ == '__main__':
    app.run(debug=False)