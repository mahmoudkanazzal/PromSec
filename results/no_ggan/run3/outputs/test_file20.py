from flask import Flask, request, jsonify
import os
import yaml
import subprocess

app = Flask(__name__)

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'placeholder_token')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.data
    try:
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    if station_id is None:
        return jsonify({'error': 'Missing station_id'}), 400
    return jsonify({'status': 'ok', 'station': station_id, 'temperature': temperature, 'humidity': humidity})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '').strip()
    if report_type not in {'summary', 'detailed'}:
        return jsonify({'error': 'Invalid report type'}), 400
    try:
        subprocess.run(['./weather_report_tool', report_type], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Report generation failed'}), 500
    return jsonify({'status': 'report generated'})

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if token == STATION_ACCESS_TOKEN:
        return jsonify({'auth': 'success'})
    return jsonify({'auth': 'failure'}), 401

if __name__ == '__main__':
    app.run(debug=False)