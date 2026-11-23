#!/usr/bin/env python3
from flask import Flask, request, Response
import os
import logging
import re
from yaml import safe_load
import MySQLdb

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    raw = request.get_data()
    if not raw:
        return Response('ERROR: No payload', status=400)
    try:
        body = raw.decode('utf-8')
    except Exception:
        return Response('ERROR: Invalid UTF-8', status=400)
    if not body.strip():
        return Response('ERROR: No payload', status=400)
    try:
        data = safe_load(body)
    except Exception:
        return Response('ERROR: Invalid YAML', status=400)
    lat = data.get('latitude')
    lon = data.get('longitude')
    dt = data.get('datetime')
    if not lat or not lon or not dt:
        return Response('ERROR: Missing required parameters', status=400)
    try:
        float(lat)
        float(lon)
    except Exception:
        return Response('ERROR: Latitude and longitude must be numeric', status=400)
    iso_regex = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$')
    if not isinstance(dt, str) or not iso_regex.match(dt):
        return Response('ERROR: Invalid datetime format', status=400)
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), passwd=os.getenv('DB_PASS'), db=os.getenv('DB_NAME'))
        cur = conn.cursor()
        sql = "SELECT * FROM temperatures WHERE datetime = %s"
        cur.execute(sql, (dt,))
        row = cur.fetchone()
        if not row:
            return Response('No matching location found', status=404)
        temperature = str(row[2])
        logging.info('Retrieved temperature: %s', temperature)
        return Response(temperature, status=200)
    except Exception as e:
        return Response(str(e), status=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)