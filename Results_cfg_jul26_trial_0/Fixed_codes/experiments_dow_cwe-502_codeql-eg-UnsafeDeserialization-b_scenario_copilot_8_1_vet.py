import os
import yaml
from flask import Flask, request, jsonify
import MySQLdb

app = Flask(__name__)

DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

def get_temperature(latitude, longitude, datetime):
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
        cursor = conn.cursor()
        query = "SELECT temperature FROM locations WHERE latitude = %s AND longitude = %s"
        cursor.execute(query, (latitude, longitude))
        temperature = cursor.fetchone()[0]
        conn.close()
        return temperature
    except Exception as e:
        return str(e)

@app.route('/get_temperature', methods=['POST'])
def get_temperature_api():
    try:
        data = yaml.safe_load(request.data)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        datetime = data.get('datetime')

        if not latitude or not longitude or not datetime:
            return jsonify({'error': 'Missing payload'}), 400

        temperature = get_temperature(latitude, longitude, datetime)

        if temperature == None:
            return jsonify({'error': 'No matching location found'}), 404

        return jsonify({'temperature': temperature}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()