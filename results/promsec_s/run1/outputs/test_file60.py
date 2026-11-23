from flask import Flask, request, make_response
import yaml
import MySQLdb
import json
import os

app = Flask(__name__)

def error_response(message, status_code):
    return make_response(json.dumps({'error': message}), status_code, {'Content-Type': 'application/json'})

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return error_response('Missing payload parameter', 400)
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError:
        return error_response('YAML parsing error', 400)
    if not isinstance(data, dict):
        return error_response('Payload must be a YAML mapping', 400)
    required_keys = {'latitude', 'longitude', 'date'}
    if set(data.keys()) != required_keys:
        missing = required_keys - set(data.keys())
        if missing:
            return error_response(f'Missing keys: {", ".join(missing)}', 400)
        return error_response('Payload must contain exactly latitude, longitude, and date', 400)
    latitude = data['latitude']
    longitude = data['longitude']
    date = data['date']
    if not isinstance(latitude, (int, float)):
        return error_response('latitude must be a number', 400)
    if not isinstance(longitude, (int, float)):
        return error_response('longitude must be a number', 400)
    if not isinstance(date, str):
        return error_response('date must be a string', 400)
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_password, db_name]):
        return error_response('Incomplete database configuration', 500)
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        query = "SELECT temperature FROM temperature_data WHERE latitude=%s AND longitude=%s AND date=%s"
        cursor.execute(query, (latitude, longitude, date))
        row = cursor.fetchone()
        if row is None:
            return error_response('No temperature data found', 404)
        temperature = row[0]
        return make_response(json.dumps({'temperature': temperature}), 200, {'Content-Type': 'application/json'})
    except MySQLdb.Error as e:
        return error_response(str(e), 500)
    except Exception as e:
        return error_response(str(e), 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)