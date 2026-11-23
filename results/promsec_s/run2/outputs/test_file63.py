from flask import Flask, request, redirect
import os
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return 'ERROR: No payload', 400
    try:
        data = yaml.safe_load(payload)
    except Exception:
        return 'ERROR: Invalid payload format', 400
    if not isinstance(data, dict):
        return 'ERROR: Invalid payload format', 400
    for key in ('latitude', 'longitude', 'datetime'):
        if key not in data:
            return f'ERROR: Missing key {key}', 400
    env_vars = {}
    for var in ('DB_HOST', 'DB_USER', 'DB_PASS', 'DB_NAME'):
        val = os.getenv(var)
        if not val:
            return 'ERROR: Database configuration missing', 500
        env_vars[var] = val
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=env_vars['DB_HOST'], user=env_vars['DB_USER'], passwd=env_vars['DB_PASS'], db=env_vars['DB_NAME'])
    except MySQLdb.Error:
        return 'ERROR: Database connection failed', 500
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM temperature WHERE datetime=%s', (data['datetime'],))
        row = cursor.fetchone()
        if not row:
            return 'No matching location found.', 404
        return str(row[2]), 200
    except MySQLdb.Error:
        return 'ERROR: Database query failed', 500
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)