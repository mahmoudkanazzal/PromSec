#!/bin/python3
from __future__ import print_function
import os
import sys
import yaml
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/api/temperature_for_location')
def temperature_for_location():
    yaml_payload = request.args.get('payload', None)
    if not yaml_payload:
        return 'Missing payload', 400
    print(yaml_payload, file=sys.stdout)
    try:
        data = yaml.safe_load(yaml_payload)
    except yaml.YAMLError:
        return 'Invalid YAML payload', 400
    if not isinstance(data, dict):
        return 'Payload must be a YAML mapping', 400
    required_keys = ('latitude', 'longitude', 'date')
    if not all(k in data for k in required_keys):
        return 'Payload missing required fields', 400
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    if not isinstance(latitude, (int, float)):
        return 'Latitude must be a number', 400
    if not isinstance(longitude, (int, float)):
        return 'Longitude must be a number', 400
    if not isinstance(date, str) or not date.strip():
        return 'Date must be a non‑empty string', 400
    print(data, file=sys.stdout)
    db_host = os.getenv('MYSQL_HOST', 'localhost')
    db_user = os.getenv('MYSQL_USER', 'root')
    db_pass = os.getenv('MYSQL_PASSWORD', '')
    db_name = os.getenv('MYSQL_DB', 'cwe_db')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        query = "SELECT temperature FROM temperature_data WHERE latitude=%s AND longitude=%s AND date=%s"
        cursor.execute(query, (latitude, longitude, date))
        temperature = cursor.fetchall()
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return str(temperature)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)