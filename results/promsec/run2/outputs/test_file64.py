from flask import Flask, request, make_response
import os
import logging
from yaml import safe_load
import MySQLdb

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    try:
        raw = request.get_data()
        if not raw:
            return make_response('ERROR: No payload', 400)
        try:
            body = raw.decode('utf-8')
        except Exception:
            return make_response('ERROR: Invalid UTF-8 payload', 400)
        if not body:
            return make_response('ERROR: No payload', 400)
        try:
            data = safe_load(body)
        except Exception:
            return make_response('ERROR: Invalid YAML payload', 400)
        lat = data.get('latitude')
        lon = data.get('longitude')
        dt = data.get('datetime')
        if not lat or not lon or not dt:
            return make_response('ERROR: Missing required parameters', 400)
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except Exception:
            return make_response('ERROR: Latitude and longitude must be numbers', 400)
        if not isinstance(dt, str) or not dt.strip():
            return make_response('ERROR: Invalid datetime', 400)
        db_host = os.getenv('DB_HOST')
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_name = os.getenv('DB_NAME')
        conn = None
        cursor = None
        try:
            conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
            cursor = conn.cursor()
            query = "SELECT * FROM temperatures WHERE datetime = %s"
            cursor.execute(query, (dt,))
            row = cursor.fetchone()
            if not row:
                return make_response('No matching location found', 404)
            temp = str(row[2])
            logging.info(f"Retrieved temperature: {temp}")
            return make_response(temp, 200)
        except MySQLdb.Error as e:
            return make_response(str(e), 500)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    except Exception as e:
        return make_response('Internal server error', 500)

if __name__ == '__main__':
    app.run(debug=False)