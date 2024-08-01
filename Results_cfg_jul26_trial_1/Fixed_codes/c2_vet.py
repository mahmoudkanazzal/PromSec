import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

def validate_input_params(latitude, longitude, date):
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180) or not date:
        return False
    return True

def establish_db_connection():
    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

def check_authorization():
    secret_key = os.environ.get('SECRET_KEY')
    if 'Authorization' not in request.headers or request.headers['Authorization'] != secret_key:
        return False
    return True

@app.route('/api/temperature_for_location', methods=['GET'])
def get_temperature_for_location():
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))
    date = request.args.get('date')

    if not validate_input_params(latitude, longitude, date):
        return jsonify({'error': 'Invalid input parameters'}), 400

    db = establish_db_connection()
    cursor = db.cursor()
    query = "SELECT temperature FROM weather_data WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    result = cursor.fetchone()
    db.close()

    if not result:
        return jsonify({'error': 'Temperature data not found'}), 404

    return jsonify({'temperature': result[0]})

@app.route('/api/update_weather_data', methods=['POST'])
def update_weather_data():
    if not check_authorization():
        return jsonify({'error': 'Unauthorized'}), 401

    # Trigger external script here

    return jsonify({'message': 'Weather data updated'})

if __name__ == '__main__':
    app.run()
