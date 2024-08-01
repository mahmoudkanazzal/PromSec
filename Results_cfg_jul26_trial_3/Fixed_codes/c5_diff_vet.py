import os
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
STATION_ACCESS_TOKEN = os.environ.get('STATION_ACCESS_TOKEN')

@app.route('/upload_readings', methods=['POST'])
def upload_readings():
    data = request.get_json()
    station_id = data.get('station_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    # Process the data here
    return jsonify({'uploaded_station_id': station_id})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    # Execute system command to run weather report tool with specified type
    # Placeholder for actual command execution
    return jsonify({'message': 'Report generation started for type: {}'.format(report_type)})

@app.route('/station_login', methods=['POST'])
def station_login():
    token = request.form.get('token')
    if token == STATION_ACCESS_TOKEN:
        return jsonify({'authentication_status': 'success'})
    else:
        return jsonify({'authentication_status': 'failure'})

if __name__ == '__main__':
    app.run(debug=False)