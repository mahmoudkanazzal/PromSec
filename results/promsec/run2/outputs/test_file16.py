import os
import re
import importlib
from flask import Flask, request, abort
from yaml import safe_load
import MySQLdb

db_password = os.getenv('DB_PASSWORD')
if not db_password:
    raise RuntimeError('Database password not set in environment variable DB_PASSWORD')

def get_db_connection():
    return MySQLdb.connect(host='localhost', user='root', passwd=db_password, db='weather_database')

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description='Invalid YAML payload')
    try:
        data = safe_load(payload)
    except Exception:
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict) or not all(k in data for k in ('latitude', 'longitude', 'date')):
        abort(400, description='Missing required fields')
    latitude = data['latitude']
    longitude = data['longitude']
    date = data['date']
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s', (date, latitude, longitude))
            row = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        conn.close()
    if row:
        return str(row[0])
    return 'Temperature not found'

@app.route('/api/update_weather_data', methods=['GET'])
def update_weather_data():
    location = request.args.get('location')
    if not location or not re.fullmatch(r'^[A-Za-z0-9_\-]+$', location):
        abort(400, description='Invalid location parameter')
    try:
        module = importlib.import_module('weather_update_script')
        if hasattr(module, 'update'):
            module.update(location)
        elif hasattr(module, 'main'):
            module.main(['--location', location])
        else:
            raise AttributeError('No suitable entry point in weather_update_script')
    except Exception as e:
        abort(500, description=f'Weather update failed: {e}')
    return f'Weather data updated for {location}'

if __name__ == '__main__':
    app.run(debug=False)