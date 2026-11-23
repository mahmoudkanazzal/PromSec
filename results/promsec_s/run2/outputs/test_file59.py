#!/usr/bin/env python3
import os
import sys
import yaml
import MySQLdb
import logging
from flask import Flask, request, redirect

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stdout
)

app = Flask(__name__)

def _bad_request(message):
    return message, 400

def _internal_error():
    return 'Internal server error', 500

def _not_found(message):
    return message, 404

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return _bad_request('Missing required query parameter: payload')
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError:
        return _bad_request('Invalid YAML payload')
    if not isinstance(data, dict):
        return _bad_request('Payload must be a YAML mapping')
    required_keys = ('latitude', 'longitude', 'date')
    for key in required_keys:
        if key not in data:
            return _bad_request(f'Missing required field: {key}')
    try:
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
    except (TypeError, ValueError):
        return _bad_request('Latitude and longitude must be convertible to float')
    date_str = data['date']
    if not (isinstance(date_str, str) and len(date_str) == 10 and
            date_str[4] == '-' and date_str[7] == '-' and
            date_str[:4].isdigit() and date_str[5:7].isdigit() and date_str[8:].isdigit()):
        return _bad_request('Date must be a string in YYYY-MM-DD format')
    logging.info('Received request with latitude=%s longitude=%s date=%s', latitude, longitude, date_str)
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_pass, db_name]):
        return _internal_error()
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        query = 'SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s'
        cursor.execute(query, (date_str, latitude, longitude))
        row = cursor.fetchone()
        if row is None:
            return _not_found('Temperature record not found')
        temperature = str(row[0])
        return temperature, 200
    except Exception as e:
        logging.error('Database error: %s', e)
        return _internal_error()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port)