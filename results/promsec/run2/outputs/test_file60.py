#!/usr/bin/env python3
import os
from flask import Flask, request, abort
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description="Missing 'payload' parameter")
    try:
        data = yaml.safe_load(payload)
    except Exception:
        abort(400, description="Invalid YAML payload")
    if not isinstance(data, dict):
        abort(400, description="Payload must be a mapping")
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    if latitude is None or longitude is None or date is None:
        abort(400, description="Missing required fields: latitude, longitude, date")
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'cwe_db')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host,
                               user=db_user,
                               passwd=db_pass,
                               db=db_name,
                               charset='utf8mb4',
                               use_unicode=True)
        cursor = conn.cursor()
        query = ("SELECT temperature FROM temperature_data "
                 "WHERE latitude=%s AND longitude=%s AND date=%s LIMIT 1")
        cursor.execute(query, (latitude, longitude, date))
        row = cursor.fetchone()
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
    if not row:
        abort(404, description="Temperature data not found")
    temperature = row[0]
    return str(temperature)

if __name__ == '__main__':
    app.run()