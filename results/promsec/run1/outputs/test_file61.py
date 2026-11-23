import os
from json import loads
import MySQLdb
from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload', '')
    if not payload or len(payload) > 10000:
        return Response('Invalid payload', status=400)
    try:
        data = loads(payload)
    except Exception:
        return Response('Invalid JSON', status=400)
    if not isinstance(data, dict):
        return Response('Invalid JSON object', status=400)
    for key in ('lat', 'lon', 'date'):
        if key not in data:
            return Response('Missing key', status=400)
    try:
        lat = int(data['lat'])
        lon = int(data['lon'])
        date = int(data['date'])
    except Exception:
        return Response('Invalid integer values', status=400)
    conn = None
    cursor = None
    try:
        password = os.getenv('DB_PASSWORD', '')
        conn = MySQLdb.connect(host='localhost', user='root', passwd=password, db='test')
        cursor = conn.cursor()
        query = "SELECT temp FROM temperatures WHERE lat=%s AND lon=%s AND date=%s LIMIT 1"
        cursor.execute(query, (lat, lon, date))
        row = cursor.fetchone()
        if row:
            return Response(str(row[0]), status=200, mimetype='text/plain')
        else:
            return Response('Not found', status=404)
    except Exception:
        return Response('Internal server error', status=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)