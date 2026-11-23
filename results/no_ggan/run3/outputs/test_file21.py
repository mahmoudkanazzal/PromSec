import os
import yaml
import subprocess
from flask import Flask, request, jsonify

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')
app = Flask(__name__)

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.get_data(as_text=True)
    data = yaml.safe_load(raw) or {}
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    return jsonify(status='Readings uploaded', station=station_id)

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '').strip()
    allowed = {'summary', 'detailed', 'full'}
    if report_type not in allowed:
        return jsonify(status='Invalid report type'), 400
    try:
        result = subprocess.run(['./weather_report_tool', report_type], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return jsonify(status='Report generation failed', error=result.stderr.strip()), 500
        return jsonify(status='Report generation started')
    except Exception as e:
        return jsonify(status='Report generation error', error=str(e)), 500

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if token == STATION_ACCESS_TOKEN:
        return jsonify(status='Station authenticated')
    return jsonify(status='Authentication failed'), 401

if __name__ == '__main__':
    app.run(debug=False)