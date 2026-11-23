#!/usr/bin/env python3
import os
import logging
from flask import Flask, request
import yaml
import MySQLdb

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    body = request.get_data(as_text=True)
    if not body:
        return 'ERROR: No payload', 400
    try:
        data = yaml.safe_load(body)
    except Exception as e:
        logging.error(str(e))
        return 'ERROR: Invalid YAML payload', 400
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    dt = data.get('datetime')
    if not latitude or not longitude or not dt:
        return 'ERROR: Missing required parameters', 400
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            passwd=os.getenv('DB_PASS'),
            db=os.getenv('DB_NAME')
        )
    except Exception as e:
        logging.error(str(e))
        return str(e), 500
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM temperature WHERE datetime=%s", (dt,))
            row = cursor.fetchone()
            if not row:
                return 'No matching location found', 404
            temp_str = str(row[2])
            logging.info('Retrieved temperature: %s' % temp_str)
            return temp_str, 200
        finally:
            cursor.close()
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)