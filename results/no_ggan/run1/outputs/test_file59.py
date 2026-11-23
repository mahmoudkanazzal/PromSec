#!/usr/bin/env python3
import os
import sys
import yaml
import MySQLdb
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'temp_database')
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)
        return conn
    except MySQLdb.Error as e:
        app.logger.error(f'Database connection error: {e}')
        abort(500, description='Database connection failed')

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description="Missing 'payload' parameter")
    try:
        data = yaml.safe_load(payload)
    except Exception as e:
        app.logger.error(f'YAML parsing error: {e}')
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict):
        abort(400, description='Invalid payload format')
    required_fields = ['latitude', 'longitude', 'date']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Missing field: {field}")
    latitude = data['latitude']
    longitude = data['longitude']
    date = data['date']
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s LIMIT 1"
        cursor.execute(query, (date, latitude, longitude))
        row = cursor.fetchone()
        if not row:
            abort(404, description='Temperature data not found')
        temp = row[0]
        return jsonify({'temperature': temp}), 200
    except MySQLdb.Error as e:
        app.logger.error(f'Database query error: {e}')
        abort(500, description='Database query failed')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port)