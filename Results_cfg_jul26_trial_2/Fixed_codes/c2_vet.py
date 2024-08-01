import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')

@app.route('/get_temperature', methods=['GET'])
def get_temperature():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    date = request.args.get('date')

    if not latitude or not longitude or not date:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = connection.cursor()

        query = "SELECT temperature FROM weather_data WHERE latitude = %s AND longitude = %s AND date = %s"
        cursor.execute(query, (latitude, longitude, date))
        temperature = cursor.fetchone()

        cursor.close()
        connection.close()

        if temperature:
            return jsonify({'temperature': temperature[0]})
        else:
            return jsonify({'error': 'Temperature data not found'}), 404

    except mysql.connector.Error as error:
        return jsonify({'error': str(error)}), 500

@app.route('/update_weather_data', methods=['POST'])
def update_weather_data():
    data = request.get_json()

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    temperature = data.get('temperature')

    if not latitude or not longitude or not date or not temperature:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = connection.cursor()

        query = "INSERT INTO weather_data (latitude, longitude, date, temperature) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (latitude, longitude, date, temperature))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Weather data updated successfully'})

    except mysql.connector.Error as error:
        return jsonify({'error': str(error)}), 500

if __name__ == '__main__':
    app.run()