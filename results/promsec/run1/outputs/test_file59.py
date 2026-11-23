#!/usr/bin/env python3
from flask import Flask, request
import os
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location')
def temperature_for_location():
    payload = request.args.get('payload')
    if not payload:
        return "Missing payload", 400
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError:
        return "Invalid YAML payload", 400
    if not isinstance(data, dict):
        return "Invalid YAML payload", 400
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    if latitude is None or longitude is None or date is None:
        return "Missing required fields", 400
    print(latitude, longitude, date)
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'temp_database')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s",
            (date, latitude, longitude)
        )
        row = cursor.fetchone()
        if not row:
            return "No temperature data found", 404
        temp = row[0]
        return str(temp)
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

if __name__ == '__main__':
    app.run()