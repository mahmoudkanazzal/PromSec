#!/bin/python3
import os
import yaml
import MySQLdb
import logging
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    raw = request.get_data()
    try:
        payload = raw.decode('utf-8')
    except Exception:
        return 'ERROR: No payload', 400
    if not payload:
        return 'ERROR: No payload', 400
    try:
        data = yaml.safe_load(payload)
    except Exception:
        return 'ERROR: Invalid YAML', 400
    if not isinstance(data, dict) or not all(k in data for k in ('latitude', 'longitude', 'datetime')):
        return 'ERROR: Missing required parameters', 400
    dt = data['datetime']
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')
    dbname = os.getenv('DB_NAME')
    if not all([host, user, password, dbname]):
        return 'Database configuration error', 500
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=password, db=dbname)
        cur = conn.cursor()
        cur.execute('SELECT * FROM temperature WHERE datetime=%s', (dt,))
        row = cur.fetchone()
        if not row:
            return 'No matching location found', 404
        temp = str(row[2])
        logging.info(f'Retrieved temperature: {temp}')
        return temp
    except MySQLdb.Error as e:
        return str(e), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)