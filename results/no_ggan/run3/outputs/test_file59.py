#!/usr/bin/env python3
import os, sys
import yaml
import MySQLdb
from flask import Flask, request, abort, jsonify

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'temp_database')

def get_db_connection():
    try:
        conn = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8mb4'
        )
        return conn
    except MySQLdb.Error as e:
        app.logger.error('Database connection error: %s', e)
        abort(500, description='Internal server error')

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description="Missing 'payload' parameter")
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError as e:
        app.logger.warning('YAML parsing error: %s', e)
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict):
        abort(400, description='Invalid YAML payload')
    for field in ('latitude', 'longitude', 'date'):
        if field not in data:
            abort(400, description=f'Missing required field: {field}')
    latitude = data['latitude']
    longitude = data['longitude']
    date = data['date']
    if not isinstance(latitude, (int, float)):
        abort(400, description='Invalid latitude value')
    if not isinstance(longitude, (int, float)):
        abort(400, description='Invalid longitude value')
    if not isinstance(date, str):
        abort(400, description='Invalid date value')
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s"
        cursor.execute(sql, (date, latitude, longitude))
        row = cursor.fetchone()
        if row is None:
            abort(404, description='Temperature data not found')
        temperature = row[0]
        return jsonify({'temperature': temperature})
    except MySQLdb.Error as e:
        app.logger.error('Database query error: %s', e)
        abort(500, description='Internal server error')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # In production, use a proper WSGI server instead of Flask's built-in server.
    app.run(host='0.0.0.0', port=5000, debug=False)