#!/usr/bin/env python3
import os
import yaml
import MySQLdb
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'temp_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'temp_database')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload_str = request.args.get('payload')
    if payload_str is None:
        abort(400, description="Missing 'payload' parameter")
    try:
        data = yaml.safe_load(payload_str)
    except Exception:
        abort(400, description="Invalid YAML payload")
    try:
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        date = data['date']
    except Exception:
        abort(400, description="Invalid payload structure")
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s"
        cursor.execute(sql, (date, latitude, longitude))
        row = cursor.fetchone()
        if row is None:
            abort(404, description="Temperature not found")
        temperature = row[0]
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    return jsonify({'temperature': temperature})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)