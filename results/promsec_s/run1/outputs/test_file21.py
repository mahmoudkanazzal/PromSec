import os, sys
from flask import Flask, request, jsonify
from yaml import safe_load

app = Flask(__name__)

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', 'weather_station_token_2023')

def constant_time_compare(a, b):
    if not isinstance(a, str) or not isinstance(b, str) or len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw = request.get_data(as_text=True)
    try:
        data = safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Payload must be a mapping'}), 400
    required = {'station_id', 'temperature', 'humidity'}
    if not required.issubset(data.keys()):
        return jsonify({'error': 'Missing required fields'}), 400
    return jsonify({'status': 'Readings uploaded', 'station': data['station_id']}), 200

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    if report_type not in ('summary', 'detailed'):
        return jsonify({'error': 'Invalid report type'}), 400
    script_dir = os.path.abspath(os.path.dirname(__file__))
    tool_path = os.path.join(script_dir, 'weather_report_tool')
    try:
        import mimetypes
        mimetypes.guess_type(tool_path)
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        return jsonify({'error': 'Failed to start report generation'}), 500
    return jsonify({'status': 'Report generation started'}), 200

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if constant_time_compare(token, STATION_ACCESS_TOKEN):
        return jsonify({'status': 'Station authenticated'}), 200
    return jsonify({'status': 'Authentication failed'}), 401

if __name__ == '__main__':
    app.run(debug=False)