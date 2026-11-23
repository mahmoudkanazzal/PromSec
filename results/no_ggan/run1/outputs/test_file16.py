#!/usr/bin/env python3
import os
import re
import yaml
import datetime
import subprocess
import MySQLdb
from flask import Flask, request, abort

def get_db_connection():
    pwd = os.getenv('DB_PASSWORD')
    if not pwd:
        raise RuntimeError('Database password not set in environment variable DB_PASSWORD')
    return MySQLdb.connect(host='localhost', user='root', passwd=pwd, db='weather_database', charset='utf8mb4', use_unicode=True)

def validate_payload(payload_str):
    try:
        data = yaml.safe_load(payload_str)
    except Exception as e:
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict):
        abort(400, description='Payload must be a dictionary')
    for key in ('latitude', 'longitude', 'date'):
        if key not in data:
            abort(400, description=f'Missing required key: {key}')
    try:
        lat = float(data['latitude'])
    except Exception:
        abort(400, description='Latitude must be a float')
    try:
        lon = float(data['longitude'])
    except Exception:
        abort(400, description='Longitude must be a float')
    try:
        dt = datetime.datetime.strptime(str(data['date']), '%Y-%m-%d')
        date_str = dt.strftime('%Y-%m-%d')
    except Exception:
        abort(400, description='Date must be in ISO format YYYY-MM-DD')
    return {'latitude': lat, 'longitude': lon, 'date': date_str}

def validate_location(location):
    if not isinstance(location, str) or not location.strip():
        abort(400, description='Location must be a non-empty string')
    if not re.fullmatch(r'^[A-Za-z0-9 _-]+$', location):
        abort(400, description='Location contains invalid characters')
    return location

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description='Missing payload parameter')
    params = validate_payload(payload)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = "SELECT temp FROM temperatures WHERE date = %s AND latitude = %s AND longitude = %s"
        cur.execute(query, (params['date'], params['latitude'], params['longitude']))
        row = cur.fetchone()
        if row:
            return str(row[0]), 200
        else:
            abort(404, description='Temperature not found')
    finally:
        if conn:
            conn.close()

@app.route('/api/update_weather_data', methods=['GET'])
def update_weather_data():
    location = request.args.get('location')
    if location is None:
        abort(400, description='Missing location parameter')
    loc = validate_location(location)
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'weather_update_script.py'))
    try:
        result = subprocess.run(
            ['python3', script_path, '--location', loc],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        abort(500, description=e.stderr or 'Subprocess failed')
    return f'Weather data updated for {loc}', 200

if __name__ == '__main__':
    app.run(debug=False)