#!/usr/bin/env python3
import os
import logging
from flask import Flask, request, jsonify
import yaml
import MySQLdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASS'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        use_unicode=True
    )

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if not payload:
        return jsonify(error="No payload provided"), 400
    try:
        data = yaml.safe_load(payload)
    except Exception as e:
        logger.warning("YAML parsing error: %s", e)
        return jsonify(error="Invalid YAML payload"), 400
    if not isinstance(data, dict):
        return jsonify(error="Missing required fields"), 400
    required_keys = ('latitude', 'longitude', 'datetime')
    if not all(key in data for key in required_keys):
        return jsonify(error="Missing required fields"), 400
    latitude = data['latitude']
    longitude = data['longitude']
    dt = data['datetime']
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return jsonify(error="Latitude and longitude must be numeric"), 400
    if not isinstance(dt, str):
        return jsonify(error="Datetime must be a string"), 400
    conn = None
    cursor = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT temperature FROM temperature WHERE datetime = %s LIMIT 1",
            (dt,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify(error="No matching record found"), 404
        temperature = row[0]
        return jsonify(temperature=temperature), 200
    except MySQLdb.Error as e:
        logger.error("Database error: %s", e)
        return jsonify(error="Internal server error"), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    # In production, use a proper WSGI server (e.g., gunicorn)
    app.run(host='0.0.0.0', port=5000)