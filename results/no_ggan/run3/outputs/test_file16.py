#!/usr/bin/env python3
import os
import re
import subprocess
import yaml
import MySQLdb
from flask import Flask, request, abort

app = Flask(__name__)

def get_db_password():
    pwd = os.getenv('DB_PASSWORD')
    if not pwd:
        raise RuntimeError('Database password not set in environment')
    return pwd

def get_db_connection():
    return MySQLdb.connect(host="localhost", user="root", passwd=get_db_password(), db="weather_database")

def validate_payload(payload):
    data = yaml.safe_load(payload)
    if not isinstance(data, dict):
        raise ValueError('Payload must be a mapping')
    for key in ('latitude', 'longitude', 'date'):
        if key not in data:
            raise ValueError(f'Missing {key}')
    try:
        data['latitude'] = float(data['latitude'])
        data['longitude'] = float(data['longitude'])
    except Exception:
        raise ValueError('Invalid latitude or longitude')
    if not isinstance(data['date'], str):
        raise ValueError('Invalid date')
    return data

def is_valid_location(loc):
    return re.fullmatch(r'[\w\s-]+', loc) is not None

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if not payload:
        abort(400, description='Missing payload')
    try:
        data = validate_payload(payload)
    except Exception as e:
        abort(400, description=str(e))
    latitude = data['latitude']
    longitude = data['longitude']
    date = data['date']
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s"
        cursor.execute(query, (date, latitude, longitude))
        row = cursor.fetchone()
        if row:
            return str(row[0])
        else:
            return "Temperature not found"
    finally:
        conn.close()

@app.route('/api/update_weather_data', methods=['GET'])
def update_weather_data():
    location = request.args.get('location')
    if not location:
        abort(400, description='Missing location')
    if not is_valid_location(location):
        abort(400, description='Invalid location')
    try:
        subprocess.run(["python3", "weather_update_script.py", "--location", location], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        abort(500, description='Weather update failed')
    return f"Weather data updated for {location}"

if __name__ == '__main__':
    app.run(debug=False)