#!/usr/bin/env python3
import os
import json
from flask import Flask, request
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload_str = request.args.get('payload')
    if payload_str is None:
        return 'ERROR: No payload', 400
    try:
        payload = json.loads(payload_str)
    except Exception:
        return 'ERROR: Invalid JSON payload', 400
    if not all(k in payload for k in ('latitude', 'longitude', 'datetime')):
        return 'ERROR: Missing required fields', 400
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_pass, db_name]):
        return 'ERROR: Database configuration missing', 500
    try:
        with MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name) as conn:
            with conn.cursor() as cursor:
                query = 'SELECT * FROM temperature WHERE datetime = %s'
                cursor.execute(query, (payload['datetime'],))
                row = cursor.fetchone()
                if row is None:
                    return 'No matching location found.', 404
                temperature = row[2]
                return str(temperature), 200
    except MySQLdb.Error:
        return 'ERROR: Database query failed', 500

if __name__ == '__main__':
    run_host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    run_port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=run_host, port=run_port)