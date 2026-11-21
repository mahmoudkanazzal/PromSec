from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

STATION_ACCESS_TOKEN = "weather_station_token_2023"

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    yaml_data = request.data.decode('utf-8')
    readings = yaml.load(yaml_data, Loader=yaml.FullLoader)
    
    station_id = readings['station_id']
    temperature = readings['temperature']
    humidity = readings['humidity']
    
    return jsonify({"status": "Readings uploaded", "station": station_id})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    os.system(f"./weather_report_tool {report_type}")
    return jsonify({"status": "Report generation started"})

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token', '')
    
    if token == STATION_ACCESS_TOKEN:
        return jsonify({"status": "Station authenticated"})
    else:
        return jsonify({"status": "Authentication failed"}), 401

if __name__ == '__main__':
    app.run(debug=False)

