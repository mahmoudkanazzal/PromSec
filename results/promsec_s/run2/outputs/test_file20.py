from flask import Flask, request, jsonify
import os
import hmac
import mimetypes
from yaml import safe_load

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1048576

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.get_data(as_text=True)
    try:
        data = safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    required = {'station_id', 'temperature', 'humidity'}
    if not required.issubset(data.keys()):
        return jsonify({'error': 'Missing required fields'}), 400
    return jsonify({'status': 'Readings uploaded', 'station': data['station_id']}), 200

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    if report_type not in ('summary', 'detailed'):
        return jsonify({'status': 'Invalid report type'}), 400
    mimetypes.guess_type(report_type)
    return jsonify({'status': 'Report generation started'}), 200

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if hmac.compare_digest(token, STATION_ACCESS_TOKEN):
        return jsonify({'status': 'Station authenticated'}), 200
    return jsonify({'status': 'Authentication failed'}), 401

if __name__ == '__main__':
    app.run(debug=False)