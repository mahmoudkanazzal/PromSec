#!/usr/bin/env python3
# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
import os
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return 'YAML payload missing from request'
    try:
        data = yaml.safe_load(payload)
    except Exception:
        return 'Invalid YAML payload'
    if not isinstance(data, dict):
        return 'Invalid YAML payload'
    try:
        lat = int(data['lat'])
        lon = int(data['lon'])
        date = int(data['date'])
    except Exception:
        return 'Invalid YAML payload'
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'appuser')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'cwe')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        query = "SELECT temp FROM temperature WHERE lat=%s AND lon=%s AND date=%s"
        cursor.execute(query, (lat, lon, date))
        row = cursor.fetchone()
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
    if row:
        return str(row[0])
    return 'No temperature data found'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)