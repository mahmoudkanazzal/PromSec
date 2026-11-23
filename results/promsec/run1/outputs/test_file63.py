#!/usr/bin/env python3
import os
import json
from flask import Flask, request, Response
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return Response('ERROR: No payload', status=400, mimetype='text/plain')
    try:
        data = json.loads(payload)
    except Exception:
        return Response('ERROR: Invalid JSON payload', status=400, mimetype='text/plain')
    if not all(k in data for k in ('latitude', 'longitude', 'datetime')):
        return Response('ERROR: Missing required fields', status=400, mimetype='text/plain')
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_pass, db_name]):
        return Response('ERROR: Database configuration missing', status=500, mimetype='text/plain')
    try:
        with MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name) as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM temperature WHERE datetime = %s"
                cursor.execute(sql, (data['datetime'],))
                row = cursor.fetchone()
                if not row:
                    return Response('No matching location found.', status=404, mimetype='text/plain')
                temperature = row[2]
                return Response(str(temperature), status=200, mimetype='text/plain')
    except MySQLdb.Error:
        return Response('ERROR: Database query failed', status=500, mimetype='text/plain')

if __name__ == "__main__":
    run_host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    run_port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=run_host, port=run_port)