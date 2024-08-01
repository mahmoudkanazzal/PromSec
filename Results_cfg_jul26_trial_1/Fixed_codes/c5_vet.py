import os
from flask import Flask, request, jsonify

app = Flask(__name__)

STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    data = request.get_json()
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    
    # Process the data
    
    response = {
        'status': 'success',
        'station_id': station_id
    }
    
    return jsonify(response)

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    
    # Execute system command to generate report
    
    response = {
        'status': 'report generation started'
    }
    
    return jsonify(response)

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token')
    
    if token == STATION_ACCESS_TOKEN:
        response = {
            'status': 'station authenticated'
        }
    else:
        response = {
            'status': 'authentication failure'
        }
    
    return jsonify(response), 401

if __name__ == '__main__':
    app.run()