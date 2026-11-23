from flask import Flask, request, make_response
import os, sys, re
import yaml
import pymysql
import pymysql.cursors

app = Flask(__name__)

def _bad_request(message):
    return make_response(message, 400)

def _not_found(message):
    return make_response(message, 404)

def _internal_error():
    return make_response('Internal server error', 500)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    try:
        payload = request.args.get('payload')
        if payload is None:
            return _bad_request('Missing payload parameter')
        try:
            data = yaml.safe_load(payload)
        except Exception:
            return _bad_request('Invalid YAML payload')
        if not isinstance(data, dict):
            return _bad_request('Payload must be a YAML mapping')
        for key in ('latitude', 'longitude', 'date'):
            if key not in data:
                return _bad_request(f'Missing key: {key}')
        latitude = data['latitude']
        longitude = data['longitude']
        date = data['date']
        if not isinstance(latitude, (int, float)):
            return _bad_request('Latitude must be a number')
        if not isinstance(longitude, (int, float)):
            return _bad_request('Longitude must be a number')
        if not isinstance(date, str):
            return _bad_request('Date must be a string')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            return _bad_request('Date must be in YYYY-MM-DD format')
        db_host = os.getenv('DB_HOST')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')
        if not all([db_host, db_user, db_password, db_name]):
            sys.stderr.write('Database configuration missing\n')
            return _internal_error()
        try:
            conn = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name, cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4', autocommit=True)
        except Exception as e:
            sys.stderr.write(str(e) + '\n')
            return _internal_error()
        try:
            with conn.cursor() as cur:
                sql = 'SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s'
                cur.execute(sql, (date, latitude, longitude))
                row = cur.fetchone()
                if not row:
                    return _not_found('Temperature data not found')
                temp = row.get('temp')
                return make_response(str(temp), 200)
        except Exception as e:
            sys.stderr.write(str(e) + '\n')
            return _internal_error()
        finally:
            conn.close()
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        return _internal_error()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)