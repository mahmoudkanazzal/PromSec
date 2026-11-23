import os
import logging
from flask import Flask, request, Response
import yaml
import MySQLdb

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    raw = request.data
    try:
        payload = raw.decode('utf-8')
    except Exception:
        return Response('ERROR: No payload', status=400)
    if not payload:
        return Response('ERROR: No payload', status=400)
    try:
        data = yaml.safe_load(payload)
    except Exception:
        return Response('ERROR: Invalid YAML', status=400)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    dt = data.get('datetime')
    if not latitude or not longitude or not dt:
        return Response('ERROR: Missing required parameters', status=400)
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_pass, db_name]):
        raise RuntimeError('Database configuration environment variables are missing')
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    except Exception as e:
        return Response(str(e), status=500)
    try:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM temperature WHERE datetime=%s', (dt,))
            row = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        conn.close()
    if not row:
        return Response('No matching location found', status=404)
    ret_val = str(row[2])
    logging.info(f'Retrieved temperature: {ret_val}')
    return Response(ret_val, status=200)

if __name__ == '__main__':
    app.run(debug=False)