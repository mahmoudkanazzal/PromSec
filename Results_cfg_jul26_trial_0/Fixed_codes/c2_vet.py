import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
SECRET_KEY = os.getenv('SECRET_KEY')

def connect_to_database():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

@app.route('/api/temperature_for_location', methods=['GET'])
def get_temperature_for_location():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    date = request.args.get('date')

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        query = "SELECT temperature FROM weather_data WHERE latitude = %s AND longitude = %s AND date = %s"
        cursor.execute(query, (latitude, longitude, date))
        temperature = cursor.fetchone()[0]
        conn.close()
        return jsonify({'temperature': temperature})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_weather_data', methods=['POST'])
def update_weather_data():
    if request.form.get('secret_key') == SECRET_KEY:
        # Run external script here
        return jsonify({'message': 'Weather data updated successfully'})
    else:
        return jsonify({'error': 'Unauthorized access'}), 401

if __name__ == '__main__':
    app.run()