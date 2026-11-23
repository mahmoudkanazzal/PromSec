import os
import json
import re
import MySQLdb
from flask import Flask, request, Response, escape

def get_db_connection():
    password = os.getenv('DB_PASSWORD')
    if not password:
        raise RuntimeError('DB_PASSWORD environment variable not set')
    user = os.getenv('DB_USER', 'weather_user')
    host = os.getenv('DB_HOST', 'localhost')
    db = os.getenv('DB_NAME', 'weather_database')
    return MySQLdb.connect(user=user, passwd=password, host=host, db=db, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)
app.debug = False

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload_str = request.args.get('payload')
    try:
        payload = json.loads(payload_str) if payload_str else {}
    except Exception:
        payload = {}
    latitude = payload.get('latitude')
    longitude = payload.get('longitude')
    date = payload.get('date')
    if latitude is None or longitude is None or date is None:
        return Response('Invalid payload', status=400, mimetype='text/plain')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = 'SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s'
        cur.execute(query, (date, latitude, longitude))
        row = cur.fetchone()
        if row:
            return Response(str(row[0]), status=200, mimetype='text/plain')
        else:
            return Response('Temperature not found', status=200, mimetype='text/plain')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/update_weather_data', methods=['GET'])
def update_weather_data():
    location = request.args.get('location', '')
    if not re.fullmatch(r'^[\w-]+$', location):
        return Response('Invalid location parameter', status=400, mimetype='text/plain')
    try:
        module = __import__('weather_update_script', fromlist=['main'])
        weather_update_main = getattr(module, 'main')
        weather_update_main(location)
        escaped_location = escape(location)
        return Response(f'Weather data updated for {escaped_location}', status=200, mimetype='text/plain')
    except Exception:
        return Response(f'Failed to update weather data for {location}', status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)