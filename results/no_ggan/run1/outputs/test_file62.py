#!/usr/bin/env python3
import os
import logging
import yaml
import MySQLdb
from flask import Flask, request, abort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description='Missing payload')
    try:
        data = yaml.safe_load(payload)
    except Exception:
        abort(400, description='Invalid YAML payload')
    for field in ('latitude', 'longitude', 'datetime'):
        if field not in data:
            abort(400, description=f'Missing required field: {field}')
    lat = data['latitude']
    lon = data['longitude']
    dt = data['datetime']
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            passwd=os.getenv('DB_PASS'),
            db=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM temperature WHERE datetime = %s", (dt,))
        row = cursor.fetchone()
        if not row:
            return "No matching location found."
        ret_val = str(row[2])
        return ret_val
    except MySQLdb.Error:
        logger.exception('Database error')
        abort(500, description='Internal server error')
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                logger.exception('Error closing cursor')
        if conn is not None:
            try:
                conn.close()
            except Exception:
                logger.exception('Error closing connection')

if __name__ == '__main__':
    app.run()