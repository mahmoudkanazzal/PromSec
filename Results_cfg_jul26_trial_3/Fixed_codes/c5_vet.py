import os
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['DEBUG'] = False

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
    
    # Execute system command to run weather report tool with specified type
    
    response = {
        'status': 'report generation started'
    }
    
    return jsonify(response)

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token')
    
    if token == STATION_ACCESS_TOKEN:
        auth_status = 'authenticated'
    else:
        auth_status = 'unauthenticated'
    
    response = {
        'authentication_status': auth_status
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run()