from flask import Flask, request, jsonify
import os
from yaml import safe_load
import hmac

app = Flask(__name__)

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.data
    try:
        text = raw.decode('utf-8')
    except Exception:
        return jsonify({'error': 'Unable to decode request body as UTF-8'}), 400
    try:
        data = safe_load(text)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Payload must be a YAML mapping'}), 400
    required = {'station_id', 'temperature', 'humidity'}
    missing = required - data.keys()
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
    return jsonify({'status': 'Readings uploaded', 'station': data['station_id']}), 200

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    allowed = {'summary', 'detailed', 'full'}
    if report_type not in allowed:
        return jsonify({'error': 'Invalid report type'}), 400
    return jsonify({'status': 'Report generation started', 'type': report_type}), 200

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token')
    if token is None:
        return jsonify({'status': 'Authentication failed'}), 401
    if hmac.compare_digest(token, STATION_ACCESS_TOKEN):
        return jsonify({'status': 'Station authenticated'}), 200
    return jsonify({'status': 'Authentication failed'}), 401

if __name__ == '__main__':
    app.run(debug=False)