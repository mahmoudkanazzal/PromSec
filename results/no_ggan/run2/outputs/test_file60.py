#!/usr/bin/env python3
import os
import sys
import yaml
import MySQLdb
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'cwe_db')
    try:
        return MySQLdb.connect(host=host, user=user, passwd=password, db=db)
    except MySQLdb.Error as e:
        app.logger.error(f'Database connection error: {e}')
        raise

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description="Missing 'payload' parameter.")
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError:
        abort(400, description="Invalid YAML payload.")
    if not isinstance(data, dict):
        abort(400, description="Invalid YAML payload.")
    for field in ('latitude', 'longitude', 'date'):
        if field not in data:
            abort(400, description=f"Missing required field: {field}")
    latitude = data['latitude']
    longitude = data['longitude']
    date = data['date']
    if not isinstance(latitude, (int, float)):
        abort(400, description="Invalid type for latitude; must be a number.")
    if not isinstance(longitude, (int, float)):
        abort(400, description="Invalid type for longitude; must be a number.")
    if not isinstance(date, str):
        abort(400, description="Invalid type for date; must be a string.")
    conn = None
    try:
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT temperature
                FROM temperature_data
                WHERE latitude = %s AND longitude = %s AND date = %s
                LIMIT 1
            """
            cursor.execute(sql, (latitude, longitude, date))
            row = cursor.fetchone()
            if not row:
                abort(404, description="Temperature data not found for the given location and date.")
            temperature = row[0] if isinstance(row, tuple) else row['temperature']
            return jsonify({'temperature': temperature})
    except MySQLdb.Error as e:
        app.logger.error(f'Database query error: {e}')
        abort(500, description="Database query failed.")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port)