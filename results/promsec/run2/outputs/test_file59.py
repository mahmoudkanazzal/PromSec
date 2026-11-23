#!/usr/bin/env python3
from flask import Flask, request, Response
import os
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location')
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return Response("Missing payload", status=400)
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError:
        return Response("Invalid YAML payload", status=400)
    if not isinstance(data, dict):
        return Response("Invalid YAML payload", status=400)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    if latitude is None or longitude is None or date is None:
        return Response("Missing required fields", status=400)
    print(latitude, longitude, date)
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', 'root')
    db_name = os.getenv('DB_NAME', 'temp_database')
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        sql = "SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s"
        cursor.execute(sql, (date, latitude, longitude))
        row = cursor.fetchone()
        if row is None:
            return Response("No temperature data found", status=404)
        temp = row[0]
        return str(temp)
    except MySQLdb.Error as e:
        return Response(f"Database error: {e}", status=500)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()