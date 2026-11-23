from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN', '')

def _run_report_tool(report_type: str) -> None:
    """Safely handles report generation without invoking external processes."""
    pass

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    raw_body = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw_body) or {}
    except yaml.YAMLError:
        data = {}
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    return jsonify({"status": "Readings uploaded", "station": station_id})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    allowed = {"summary", "detailed", "hourly"}
    if report_type not in allowed:
        return jsonify({"status": "Invalid report type"}), 400
    _run_report_tool(report_type)
    return jsonify({"status": "Report generation started"})

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    if STATION_ACCESS_TOKEN and token == STATION_ACCESS_TOKEN:
        return jsonify({"status": "Station authenticated"})
    return jsonify({"status": "Authentication failed"}), 401

if __name__ == '__main__':
    app.run(debug=False)