import os
import logging
import yaml
import MySQLdb
from flask import Flask, request, jsonify, make_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)

def _get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASS'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        use_unicode=True
    )

def _validate_float(value, name):
    try:
        float(value)
    except Exception:
        raise ValueError(f'Invalid {name}: must be a number.')

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    raw_body = request.get_data()
    if not raw_body:
        return make_response('ERROR: No payload', 400)
    try:
        payload_str = raw_body.decode('utf-8')
    except Exception:
        return make_response('ERROR: Invalid UTF-8 payload', 400)
    try:
        data = yaml.safe_load(payload_str)
    except yaml.YAMLError:
        return make_response('ERROR: Invalid YAML payload', 400)
    if not isinstance(data, dict):
        return make_response('ERROR: Invalid YAML payload', 400)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    datetime_val = data.get('datetime')
    if latitude is None or longitude is None or datetime_val is None:
        return make_response('ERROR: Missing required parameters', 400)
    try:
        _validate_float(latitude, 'latitude')
        _validate_float(longitude, 'longitude')
    except ValueError as e:
        return make_response(str(e), 400)
    if not isinstance(datetime_val, str) or not datetime_val.strip():
        return make_response('ERROR: Invalid datetime value', 400)
    conn = None
    cursor = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM temperature WHERE datetime = %s"
        cursor.execute(query, (datetime_val,))
        row = cursor.fetchone()
        if not row:
            return make_response('No matching location found', 404)
        temperature = str(row[2])
        logging.info("Retrieved temperature: %s for datetime %s (lat: %s, lon: %s)", temperature, datetime_val, latitude, longitude)
        return jsonify({'temperature': temperature})
    except MySQLdb.Error as e:
        logging.error('Database error: %s', e)
        return make_response('Internal server error', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)