import os
import re
import logging
import mimetypes
import yaml
import MySQLdb
from flask import Flask, request, abort, jsonify

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

DB_HOST = 'localhost'
DB_USER = 'weather_user'
DB_NAME = 'weather_db'

def get_db_password():
    pwd = os.getenv('DB_PASSWORD')
    if not pwd:
        raise RuntimeError('Environment variable DB_PASSWORD is required')
    return pwd

def validate_payload(data):
    if not isinstance(data, dict):
        return False
    required = {'latitude', 'longitude', 'date'}
    if not required.issubset(data.keys()):
        return False
    if not isinstance(data['latitude'], (int, float)):
        return False
    if not isinstance(data['longitude'], (int, float)):
        return False
    if not isinstance(data['date'], str):
        return False
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', data['date']):
        return False
    return True

def validate_location(loc):
    return isinstance(loc, str) and re.fullmatch(r'^[A-Za-z0-9_-]+$', loc) is not None

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload_str = request.args.get('payload')
    if payload_str is None:
        abort(400)
    try:
        data = yaml.safe_load(payload_str)
    except Exception:
        abort(400)
    if not validate_payload(data):
        abort(400)
    conn = None
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=get_db_password(), db=DB_NAME, charset='utf8mb4', use_unicode=True)
        cursor = conn.cursor()
        query = "SELECT temperature FROM weather WHERE latitude=%s AND longitude=%s AND date=%s"
        cursor.execute(query, (data['latitude'], data['longitude'], data['date']))
        row = cursor.fetchone()
        if row:
            return jsonify({'temperature': row[0]})
        else:
            abort(404)
    except Exception:
        logging.exception('Error retrieving temperature')
        abort(500)
    finally:
        if conn:
            conn.close()

@app.route('/api/update_weather_data', methods=['GET'])
def update_weather_data():
    location = request.args.get('location')
    if not location or not validate_location(location):
        abort(400)
    try:
        mime_type = mimetypes.guess_type(location)[0]
        if mime_type:
            return jsonify({'output': f'Guessed MIME type: {mime_type}'})
        else:
            return jsonify({'output': 'No MIME type found'})
    except Exception:
        logging.exception('Error processing update')
        abort(500)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)