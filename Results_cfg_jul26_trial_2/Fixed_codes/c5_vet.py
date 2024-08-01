import os
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
STATION_ACCESS_TOKEN = os.getenv('STATION_ACCESS_TOKEN')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    data = request.get_json()
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    
    # Process the data
    
    return jsonify({'status': 'success', 'station_id': station_id})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    
    # Execute system command to run weather report tool with specified type
    
    return jsonify({'message': 'Report generation has started'})

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token')
    
    if token == STATION_ACCESS_TOKEN:
        return jsonify({'message': 'Authentication successful'})
    else:
        return jsonify({'message': 'Authentication failed'}), 401

if __name__ == '__main__':
    app.run(debug=False)