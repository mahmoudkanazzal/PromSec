import os
import subprocess
import yaml
from flask import Flask, request, jsonify, abort

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')
ALLOWED_REPORT_TYPES = {'summary', 'detailed', 'hourly', 'daily'}

app = Flask(__name__)

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError('Payload must be a YAML mapping')
        station_id = data.get('station_id')
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        if station_id is None or temperature is None or humidity is None:
            raise ValueError('Missing required fields')
        return jsonify({'status': 'Readings uploaded', 'station': station_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '').lower()
    if report_type not in ALLOWED_REPORT_TYPES:
        return jsonify({'error': 'Invalid report type'}), 400
    try:
        result = subprocess.run(['./weather_report_tool', report_type], check=True, capture_output=True, text=True)
        return jsonify({'status': 'Report generated', 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.stderr}), 500
    except FileNotFoundError:
        return jsonify({'error': 'Report tool not found'}), 500

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token')
    if token == STATION_ACCESS_TOKEN:
        return jsonify({'status': 'Station authenticated'})
    else:
        return jsonify({'status': 'Authentication failed'}), 401

if __name__ == '__main__':
    app.run(debug=False)