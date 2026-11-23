import os
import re
import json
import logging
import secrets
import ssl
from datetime import datetime, timezone
from contextlib import closing
from flask import Flask, request, jsonify, abort
import MySQLdb

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        raise RuntimeError(f'Environment variable {var_name} is required')
    return value

def _get_ssl_params():
    ca = os.getenv('DB_SSL_CA')
    if ca:
        return {'ca': ca}
    return None

def get_db_connection():
    ssl_params = _get_ssl_params()
    conn_kwargs = {
        'host': _require_env('DB_HOST'),
        'user': _require_env('DB_USER'),
        'passwd': _require_env('DB_PASS'),
        'db': _require_env('DB_NAME'),
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': True
    }
    if ssl_params:
        conn_kwargs['ssl'] = ssl_params
    return MySQLdb.connect(**conn_kwargs)

ISO8601_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$')

def validate_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError('Payload must be a JSON object')
    try:
        latitude = data['latitude']
        longitude = data['longitude']
        dt_str = data['datetime']
    except KeyError as e:
        raise ValueError(f'Missing field: {e.args[0]}')
    if not isinstance(latitude, (int, float)):
        raise ValueError('Latitude must be a number')
    if not isinstance(longitude, (int, float)):
        raise ValueError('Longitude must be a number')
    if not isinstance(dt_str, str):
        raise ValueError('Datetime must be a string')
    if not ISO8601_REGEX.match(dt_str):
        raise ValueError('Datetime format is invalid')
    original = dt_str
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1]
        tz = timezone.utc
    else:
        tz = None
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        if tz:
            dt = dt.replace(tzinfo=tz)
    except Exception:
        raise ValueError('Datetime parsing failed')
    return {'latitude': latitude, 'longitude': longitude, 'datetime': original}

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    if not request.is_json:
        return jsonify(error='Unsupported Media Type'), 415
    try:
        payload = request.get_json()
    except Exception:
        logger.warning('Failed to parse JSON payload')
        return jsonify(error='Invalid JSON'), 400
    try:
        validated = validate_payload(payload)
    except ValueError as e:
        logger.warning(f'Payload validation error: {e}')
        return jsonify(error='Invalid payload'), 400
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT temperature FROM temperature WHERE datetime = %s', (validated['datetime'],))
                row = cur.fetchone()
                if not row:
                    return jsonify(error='Temperature not found'), 404
                temperature = row[0]
                return jsonify(temperature=temperature), 200
    except MySQLdb.Error:
        logger.exception('Database error')
        return jsonify(error='Internal server error'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)