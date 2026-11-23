#!/usr/bin/env python3
import os
import yaml
import MySQLdb
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 10

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'cwe_db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description="Missing 'payload' parameter.")
    try:
        data = yaml.safe_load(payload)
    except Exception as e:
        abort(400, description="Invalid YAML payload.")
    if not isinstance(data, dict):
        abort(400, description="Payload must be a mapping.")
    try:
        latitude = float(data['latitude'])
    except Exception:
        abort(400, description="Invalid or missing 'latitude'.")
    try:
        longitude = float(data['longitude'])
    except Exception:
        abort(400, description="Invalid or missing 'longitude'.")
    try:
        date = str(data['date'])
    except Exception:
        abort(400, description="Invalid or missing 'date'.")
    conn = None
    try:
        conn = _get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT temperature FROM temperature_data WHERE latitude=%s AND longitude=%s AND date=%s LIMIT 1"
            cursor.execute(sql, (latitude, longitude, date))
            row = cursor.fetchone()
            if not row:
                abort(404, description="Temperature data not found.")
            temperature = row[0]
    except MySQLdb.Error as e:
        abort(500, description=str(e))
    finally:
        if conn:
            conn.close()
    return jsonify({
        'latitude': latitude,
        'longitude': longitude,
        'date': date,
        'temperature': temperature
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)