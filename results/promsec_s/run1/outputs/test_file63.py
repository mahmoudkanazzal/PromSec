#!/bin/python3
# assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname
from flask import Flask, request
import os
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location')
def temperature_for_location():
    payload = request.args.get('payload')
    if not payload:
        return 'ERROR: No payload'
    data = yaml.safe_load(payload)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    dt = data.get('datetime')
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_pass, db_name]):
        return 'Database configuration error'
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name, charset='utf8mb4')
    except Exception as e:
        return str(e)
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM temperature WHERE datetime = %s', (dt,))
        row = cur.fetchone()
        if not row:
            return 'No matching location found.'
        return str(row[2])
    finally:
        try:
            cur.close()
        except:
            pass
        conn.close()