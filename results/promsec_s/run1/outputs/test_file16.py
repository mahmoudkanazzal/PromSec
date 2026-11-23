import os
import re
import yaml
import MySQLdb
from flask import Flask, request, Response, abort

db_password = os.getenv('DB_PASSWORD')
if not db_password:
    raise RuntimeError('Environment variable DB_PASSWORD is required')

app = Flask(__name__)

def get_db_connection():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_name = os.getenv('DB_NAME', 'weather_database')
    return MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)

date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
location_pattern = re.compile(r'^[A-Za-z0-9_-]+$')

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(Response('Missing payload parameter', status=400))
    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError:
        abort(Response('Invalid YAML payload', status=400))
    if not isinstance(data, dict):
        abort(Response('Payload must be a mapping', status=400))
    for key in ('latitude', 'longitude', 'date'):
        if key not in data:
            abort(Response(f'Missing key: {key}', status=400))
    latitude = data['latitude']
    longitude = data['longitude']
    date = data['date']
    if not isinstance(latitude, (int, float)):
        abort(Response('Latitude must be a number', status=400))
    if not isinstance(longitude, (int, float)):
        abort(Response('Longitude must be a number', status=400))
    if not isinstance(date, str) or not date_pattern.fullmatch(date):
        abort(Response('Date must be a string in YYYY-MM-DD format', status=400))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s', (date, latitude, longitude))
        row = cursor.fetchone()
        if row:
            return Response(str(row[0]), mimetype='text/plain')
        else:
            abort(Response('Temperature not found', status=404))
    except MySQLdb.Error:
        abort(Response('Database error', status=500))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/update_weather_data', methods=['GET'])
def update_weather_data():
    location = request.args.get('location')
    if not location or not location_pattern.fullmatch(location):
        abort(Response('Invalid location parameter', status=400))
    return Response(f'Weather data updated for {location}', mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=False)