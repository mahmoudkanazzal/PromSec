#!/usr/bin/env python3
import os
import re
import subprocess
import yaml
from flask import Flask, request, abort
import MySQLdb

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD')
if DB_PASSWORD is None:
    raise RuntimeError('Database password not set in environment variable DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'weather_database')

def get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True
    )

def validate_payload(payload_str):
    try:
        data = yaml.safe_load(payload_str)
    except Exception:
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict):
        abort(400, description='Payload must be a mapping')
    required = {'latitude', 'longitude', 'date'}
    missing = required - data.keys()
    if missing:
        abort(400, description='Missing required fields: ' + ','.join(sorted(missing)))
    try:
        data['latitude'] = float(data['latitude'])
        data['longitude'] = float(data['longitude'])
        data['date'] = str(data['date'])
    except Exception:
        abort(400, description='Invalid field types in payload')
    return data

def is_valid_location(loc):
    return re.fullmatch(r'^[A-Za-z0-9_-]+$', loc) is not None

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload_str = request.args.get('payload')
    if payload_str is None:
        abort(400, description="Missing 'payload' parameter")
    payload = validate_payload(payload_str)
    latitude = payload['latitude']
    longitude = payload['longitude']
    date = payload['date']
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s',
            (date, latitude, longitude)
        )
        row = cursor.fetchone()
    finally:
        conn.close()
    if row:
        return str(row[0])
    else:
        return 'Temperature not found', 404

@app.route('/api/update_weather_data', methods=['GET'])
def update_weather_data():
    location = request.args.get('location')
    if location is None:
        abort(400, description="Missing 'location' parameter")
    if not is_valid_location(location):
        abort(400, description='Invalid location format')
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'weather_update_script.py'))
    try:
        subprocess.run(
            ['python3', script_path, '--location', location],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        abort(500, description='Failed to update weather data')
    return f'Weather data updated for {location}'

if __name__ == '__main__':
    app.run(debug=False)