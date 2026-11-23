from flask import Flask, request
import MySQLdb
from yaml import safe_load
from os import getenv

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return 'ERROR: No payload'
    try:
        data = safe_load(payload)
    except Exception as e:
        return f'ERROR: Invalid YAML: {e}'
    if not isinstance(data, dict):
        return 'ERROR: Payload is not a dictionary'
    for key in ('latitude', 'longitude', 'datetime'):
        if key not in data:
            return f'ERROR: Missing key: {key}'
    lat = data['latitude']
    lon = data['longitude']
    dt = data['datetime']
    for var in ('DB_HOST', 'DB_USER', 'DB_PASS', 'DB_NAME'):
        val = getenv(var)
        if not val:
            return f'ERROR: Missing environment variable: {var}'
        if var == 'DB_HOST':
            host = val
        elif var == 'DB_USER':
            user = val
        elif var == 'DB_PASS':
            passwd = val
        elif var == 'DB_NAME':
            db = val
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM temperature WHERE datetime = %s', (dt,))
        row = cursor.fetchone()
        if not row:
            return 'No matching location found.'
        return str(row[2])
    except Exception as e:
        return str(e)
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)