#!/usr/bin/env python3
from flask import Flask, request, redirect
import os
import sys
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return 'ERROR: No payload', 400
    try:
        data = yaml.safe_load(payload)
    except Exception:
        return 'ERROR: Invalid payload format', 400
    if not isinstance(data, dict):
        return 'ERROR: Invalid payload format', 400
    for key in ('latitude', 'longitude', 'datetime'):
        if key not in data:
            return f'ERROR: Missing key {key}', 400
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_pass, db_name]):
        return 'ERROR: Database configuration missing', 500
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM temperature WHERE datetime=%s', (data['datetime'],))
        except Exception:
            return 'ERROR: Database query failed', 500
        row = cur.fetchone()
        if row is None:
            return 'No matching location found.', 404
        temperature = str(row[2])
        return temperature, 200
    except Exception:
        return 'ERROR: Database connection failed', 500
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)