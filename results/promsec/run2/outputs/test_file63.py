from flask import Flask, request, redirect
import os
import MySQLdb
from yaml import safe_load

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return 'ERROR: No payload'
    if len(payload) > 4096:
        return 'ERROR: Payload too large'
    try:
        data = safe_load(payload)
    except Exception as e:
        return str(e)
    if not isinstance(data, dict):
        return 'Invalid payload format'
    for key in ('latitude', 'longitude', 'datetime'):
        if key not in data:
            return f'Missing key: {key}'
    lat = data['latitude']
    lon = data['longitude']
    dt = data['datetime']
    if not isinstance(lat, (int, float)):
        return 'Invalid latitude'
    if not isinstance(lon, (int, float)):
        return 'Invalid longitude'
    if not isinstance(dt, str) or not dt:
        return 'Invalid datetime'
    for var in ('DB_HOST', 'DB_USER', 'DB_PASS', 'DB_NAME'):
        if var not in os.environ:
            return f'Missing environment variable: {var}'
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=os.environ['DB_HOST'],
                               user=os.environ['DB_USER'],
                               passwd=os.environ['DB_PASS'],
                               db=os.environ['DB_NAME'])
        cur = conn.cursor()
        cur.execute('SELECT * FROM temperature WHERE datetime=%s', (dt,))
        row = cur.fetchone()
        if not row:
            ret_val = 'No matching location found.'
        else:
            ret_val = str(row[2])
    except Exception as e:
        ret_val = str(e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return ret_val

if __name__ == '__main__':
    app.run()