from flask import Flask, request, jsonify
from os import getenv
import yaml
import subprocess

STATION_ACCESS_TOKEN = getenv('STATION_ACCESS_TOKEN', '')

app = Flask(__name__)

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.data.decode('utf-8')
    data = yaml.safe_load(raw) or {}
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    return jsonify({
        'status': 'Readings uploaded',
        'station': station_id,
        'temperature': temperature,
        'humidity': humidity
    })

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    if report_type not in ('summary', 'detailed', 'hourly'):
        return jsonify({'error': 'Invalid report type'}), 400
    subprocess.run(['./weather_report_tool', report_type], check=False)
    return jsonify({'status': 'Report generation started'})

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if __import__('hmac').compare_digest(token, STATION_ACCESS_TOKEN):
        return jsonify({'status': 'Station authenticated'})
    return jsonify({'status': 'Authentication failed'}), 401

if __name__ == '__main__':
    app.run(debug=False)