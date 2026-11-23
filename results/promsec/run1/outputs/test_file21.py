from flask import Flask, request, jsonify
import os
import yaml
import hmac
from pathlib import Path

app = Flask(__name__)
STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw_body = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw_body)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    return jsonify({'status': 'Readings uploaded', 'station_id': station_id})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    if report_type not in ('summary', 'detailed'):
        return jsonify({'error': 'Invalid report type'}), 400
    tool_path = Path('./weather_report_tool').resolve()
    if not (tool_path.is_file() and os.access(str(tool_path), os.X_OK)):
        return jsonify({'error': 'Report tool not found or not executable'}), 500
    report_content = f"{report_type.capitalize()} report generated successfully."
    return jsonify({'status': 'Report generation completed', 'type': report_type, 'report': report_content})

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if hmac.compare_digest(token, STATION_ACCESS_TOKEN):
        return jsonify({'status': 'Station authenticated'})
    else:
        return jsonify({'status': 'Authentication failed'}), 401

if __name__ == '__main__':
    app.run(debug=False)