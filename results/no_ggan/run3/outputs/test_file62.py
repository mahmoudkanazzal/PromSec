#!/usr/bin/env python3
import os
import logging
import yaml
import MySQLdb
from flask import Flask, request, jsonify, abort

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    raw = request.get_data(as_text=True)
    if not raw:
        return jsonify(error='Missing payload'), 400
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        logging.warning('Invalid YAML payload')
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict) or not all(k in data for k in ('latitude', 'longitude', 'datetime')):
        return jsonify(error='Missing required fields'), 400
    dt = data['datetime']
    db = None
    try:
        db = MySQLdb.connect(host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), passwd=os.getenv('DB_PASS'), db=os.getenv('DB_NAME'))
        with db.cursor() as cur:
            cur.execute('SELECT temperature FROM temperature WHERE datetime = %s', (dt,))
            row = cur.fetchone()
            if not row:
                return jsonify(error='Temperature not found'), 404
            temperature = row[0]
    except Exception:
        logging.error('Database operation failed')
        return jsonify(error='Database error'), 500
    finally:
        if db:
            db.close()
    return jsonify(temperature=temperature), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)