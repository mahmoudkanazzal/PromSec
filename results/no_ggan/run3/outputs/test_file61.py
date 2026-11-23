import os
import sys
import math
import logging
import contextlib
import MySQLdb
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

app = Flask(__name__)

secret_key = os.getenv('FLASK_SECRET_KEY')
if not secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable is required')
app.secret_key = secret_key

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Strict may be used if appropriate
cookie_secure_env = os.getenv('FLASK_COOKIE_SECURE')
app.config['SESSION_COOKIE_SECURE'] = False if cookie_secure_env == '0' else True

app.config['MAX_CONTENT_LENGTH'] = 4096
app.config['PREFERRED_URL_SCHEME'] = 'https'


def _env_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    if value == '1':
        return True
    if value == '0':
        return False
    return default


def _get_db_connection():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        raise RuntimeError('DB_PASSWORD environment variable is required')
    db_name = os.getenv('DB_NAME', 'cwe')
    db_ssl_ca = os.getenv('DB_SSL_CA')
    db_ssl_required = os.getenv('DB_SSL_REQUIRED')
    if db_ssl_required not in (None, '0', '1'):
        raise RuntimeError("DB_SSL_REQUIRED must be '0', '1', or unset")
    ssl_required = _env_bool(db_ssl_required, default=False)

    ssl_params = {}
    if db_ssl_ca:
        ssl_params['ca'] = db_ssl_ca
    if ssl_required:
        if not db_ssl_ca:
            raise RuntimeError('DB_SSL_CA is required when DB_SSL_REQUIRED is set')
        ssl_params['verify_cert'] = True
        ssl_params['check_hostname'] = True

    try:
        conn = MySQLdb.connect(
            host=db_host,
            user=db_user,
            passwd=db_password,
            db=db_name,
            charset='utf8mb4',
            use_unicode=True,
            autocommit=True,
            connect_timeout=10,
            ssl=ssl_params if ssl_params else None
        )
        return conn
    except MySQLdb.Error as e:
        logger.exception('Database connection error')
        raise


def _validate_coordinates(lat, lon):
    if not isinstance(lat, (int, float)):
        raise ValueError('Latitude must be a number')
    if not isinstance(lon, (int, float)):
        raise ValueError('Longitude must be a number')
    if not math.isfinite(lat):
        raise ValueError('Latitude must be finite')
    if not math.isfinite(lon):
        raise ValueError('Longitude must be finite')
    if not -90 <= lat <= 90:
        raise ValueError('Latitude must be between -90 and 90')
    if not -180 <= lon <= 180:
        raise ValueError('Longitude must be between -180 and 180')


def _validate_date(date):
    if not isinstance(date, int):
        raise ValueError('Date must be an integer')
    if date <= 0:
        raise ValueError('Date must be a positive integer')


@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400
    try:
        payload = request.get_json()
        if not isinstance(payload, dict):
            raise ValueError('JSON payload must be an object')
        lat = float(payload['lat'])
        lon = float(payload['lon'])
        date = int(payload['date'])
        _validate_coordinates(lat, lon)
        _validate_date(date)
    except (KeyError, TypeError, ValueError) as e:
        logger.info('Validation error: %s', e)
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Invalid request payload'}), 400

    try:
        with contextlib.closing(_get_db_connection()) as conn:
            with contextlib.closing(conn.cursor()) as cur:
                query = """
                SELECT temp FROM temperature
                WHERE lat = %s AND lon = %s AND date = %s
                LIMIT 1
                """
                cur.execute(query, (lat, lon, date))
                row = cur.fetchone()
                if not row:
                    return jsonify({'error': 'No temperature data found'}), 404
                temperature = row[0]
                return jsonify({'temperature': temperature}), 200
    except MySQLdb.Error:
        logger.exception('Database query error')
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port_str = os.getenv('FLASK_PORT', '5000')
    try:
        port = int(port_str)
    except ValueError:
        raise RuntimeError('FLASK_PORT must be an integer')
    app.run(host=host, port=port, use_reloader=False, threaded=True)