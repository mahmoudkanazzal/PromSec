import os
import logging
import json
from datetime import datetime
import MySQLdb
from flask import Flask, request, Response

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
required_env = ('DB_HOST', 'DB_USER', 'DB_PASS', 'DB_NAME')
missing = [var for var in required_env if not os.getenv(var)]
if missing:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

def _parse_iso_datetime(dt_str: str) -> datetime:
    try:
        return datetime.fromisoformat(dt_str)
    except Exception as e:
        raise ValueError("Invalid ISO-8601 datetime string") from e

def _validate_coordinates(lat, lon):
    try:
        lat_f = float(lat)
    except Exception:
        raise ValueError("Latitude must be a numeric value")
    try:
        lon_f = float(lon)
    except Exception:
        raise ValueError("Longitude must be a numeric value")
    if not (-90 <= lat_f <= 90):
        raise ValueError("Latitude out of range (-90 to 90)")
    if not (-180 <= lon_f <= 180):
        raise ValueError("Longitude out of range (-180 to 180)")
    return lat_f, lon_f

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    if not request.headers.get('Content-Type', '').startswith('application/json'):
        return Response('ERROR: Content-Type must be application/json', status=400, mimetype='text/plain')
    try:
        data = request.get_json()
    except Exception:
        logging.exception("JSON parsing error")
        return Response('ERROR: Invalid JSON payload', status=400, mimetype='text/plain')
    if not isinstance(data, dict):
        return Response('ERROR: Missing required parameters', status=400, mimetype='text/plain')
    required_keys = ('latitude', 'longitude', 'datetime')
    if not all(key in data for key in required_keys):
        return Response('ERROR: Missing required parameters', status=400, mimetype='text/plain')
    try:
        _validate_coordinates(data['latitude'], data['longitude'])
        dt = _parse_iso_datetime(data['datetime'])
    except ValueError as ve:
        return Response(f'ERROR: {ve}', status=400, mimetype='text/plain')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), passwd=os.getenv('DB_PASS'), db=os.getenv('DB_NAME'), charset='utf8mb4', use_unicode=True)
        cursor = conn.cursor()
        query = "SELECT * FROM temperature WHERE datetime = %s"
        cursor.execute(query, (dt,))
        row = cursor.fetchone()
        if not row:
            return Response('No matching location found', status=404, mimetype='text/plain')
        temperature = str(row[2])
        logging.debug(f"Temperature: {temperature}")
        return Response(temperature, status=200, mimetype='text/plain')
    except MySQLdb.Error:
        logging.exception("Database error")
        return Response('Internal server error', status=500, mimetype='text/plain')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)