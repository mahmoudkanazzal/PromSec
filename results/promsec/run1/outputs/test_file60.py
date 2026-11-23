from flask import Flask, request, abort
import os
import yaml
import MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location')
def temperature_for_location():
    payload = request.args.get('payload')
    if payload is None:
        abort(400, description="Missing 'payload' parameter")
    try:
        data = yaml.safe_load(payload)
    except Exception as e:
        abort(400, description=f"Invalid YAML payload: {e}")
    if not isinstance(data, dict):
        abort(400, description="Invalid YAML payload: expected a mapping")
    try:
        latitude = data['latitude']
        longitude = data['longitude']
        date = data['date']
    except KeyError:
        abort(400, description="Payload must contain 'latitude', 'longitude', and 'date' fields")
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'cwe_db')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name, charset='utf8mb4', use_unicode=True)
        cursor = conn.cursor()
        query = "SELECT temperature FROM temperature_data WHERE latitude = %s AND longitude = %s AND date = %s LIMIT 1"
        cursor.execute(query, (latitude, longitude, date))
        row = cursor.fetchone()
        temperature = row[0] if row else None
    except MySQLdb.Error as e:
        abort(500, description=f"Database error: {e}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
    if temperature is None:
        abort(404, description="Temperature data not found for the given location and date")
    return str(temperature)

if __name__ == '__main__':
    app.run()