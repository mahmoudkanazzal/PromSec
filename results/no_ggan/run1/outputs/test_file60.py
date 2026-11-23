#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify, abort
import yaml
import MySQLdb

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'cwe_db')

def _get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True
    )

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload_str = request.args.get('payload')
    if payload_str is None:
        abort(400, description='Missing required query parameter: payload')
    try:
        data = yaml.safe_load(payload_str)
    except Exception as e:
        abort(400, description=f'YAML parsing error: {e}')
    if not isinstance(data, dict):
        abort(400, description='Payload must be a YAML mapping')
    for key in ('latitude', 'longitude', 'date'):
        if key not in data:
            abort(400, description=f'Missing required key: {key}')
    try:
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        date = str(data['date'])
    except Exception as e:
        abort(400, description=f'Invalid data types: {e}')
    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cur:
                sql = """
                    SELECT temperature
                    FROM temperature_data
                    WHERE latitude = %s AND longitude = %s AND date = %s
                    LIMIT 1
                """
                cur.execute(sql, (latitude, longitude, date))
                row = cur.fetchone()
    except MySQLdb.Error as e:
        abort(500, description=f'Database error: {e}')
    if not row:
        abort(404, description='Temperature data not found for the given location and date')
    temperature = row[0]
    return jsonify({
        'latitude': latitude,
        'longitude': longitude,
        'date': date,
        'temperature': temperature
    })

if __name__ == '__main__':
    # In production, use a WSGI server instead of Flask's built-in server.
    app.run(host='0.0.0.0', port=5000)