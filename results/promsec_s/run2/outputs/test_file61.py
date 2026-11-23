#!/usr/bin/env python3
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
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
        return "YAML payload missing from request", 200, {'Content-Type': 'text/plain'}
    try:
        data = yaml.safe_load(payload)
    except Exception:
        return "Invalid YAML payload", 200, {'Content-Type': 'text/plain'}
    if not isinstance(data, dict):
        return "Invalid YAML payload", 200, {'Content-Type': 'text/plain'}
    for key in ('lat', 'lon', 'date'):
        if key not in data:
            return f"Missing {key} in payload", 200, {'Content-Type': 'text/plain'}
    try:
        lat_raw = data['lat']
        if isinstance(lat_raw, int):
            lat = lat_raw
        elif isinstance(lat_raw, str):
            lat_str = lat_raw.strip()
            if lat_str.lstrip('-').isdigit():
                lat = int(lat_str)
            else:
                raise ValueError
        else:
            raise ValueError
        lon = int(data['lon'])
        date = int(data['date'])
    except Exception:
        return "Invalid input for lat, lon, or date", 200, {'Content-Type': 'text/plain'}
    password = os.getenv('MYSQL_PASSWORD', '')
    try:
        conn = MySQLdb.connect(host='localhost', user='root', passwd=password, db='cwe')
    except MySQLdb.Error:
        return "Database error", 200, {'Content-Type': 'text/plain'}
    try:
        cursor = conn.cursor()
        try:
            query = "SELECT temp FROM temperature WHERE lat=%s AND lon=%s AND date=%s;"
            cursor.execute(query, (lat, lon, date))
            row = cursor.fetchone()
            if row is None:
                return "No temperature data found", 200, {'Content-Type': 'text/plain'}
            return str(row[0]), 200, {'Content-Type': 'text/plain'}
        finally:
            cursor.close()
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)