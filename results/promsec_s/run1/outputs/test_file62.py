from flask import Flask, request
import os
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location')
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        return 'ERROR: No payload'
    try:
        data = yaml.safe_load(payload)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        dt = data.get('datetime')
    except Exception as e:
        return str(e)
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')
    dbname = os.getenv('DB_NAME')
    if not all([host, user, password, dbname]):
        return 'Database configuration error'
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=password, db=dbname, charset='utf8mb4')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM temperature WHERE datetime=%s", (dt,))
        row = cursor.fetchone()
        if not row:
            return 'No matching location found.'
        return str(row[2])
    except Exception as e:
        return str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run()