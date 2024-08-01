import os
from flask import Flask, request, jsonify
import yaml
import pymysql

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

def get_temperature_for_location(latitude, longitude, datetime):
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cursor = conn.cursor()
        query = "SELECT temperature FROM temperature WHERE latitude = %s AND longitude = %s AND datetime = %s"
        cursor.execute(query, (latitude, longitude, datetime))
        temperature = cursor.fetchone()[0]
        conn.close()
        return temperature
    except Exception as e:
        return str(e)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    try:
        data = yaml.safe_load(request.data)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        datetime = data.get('datetime')
        
        if not latitude or not longitude or not datetime:
            return jsonify({'error': 'Missing parameters'}), 400
        
        temperature = get_temperature_for_location(latitude, longitude, datetime)
        
        if isinstance(temperature, str):
            return jsonify({'error': 'Database connection error'}), 500
        
        return jsonify({'temperature': temperature})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()