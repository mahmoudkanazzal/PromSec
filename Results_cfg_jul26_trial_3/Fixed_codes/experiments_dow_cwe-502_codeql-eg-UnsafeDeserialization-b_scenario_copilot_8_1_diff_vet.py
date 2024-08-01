import os
import yaml
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_temperature_for_location(latitude, longitude, datetime):
    try:
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                      host=DB_HOST, database=DB_NAME)
        cursor = cnx.cursor()
        query = ("SELECT temperature FROM temperatures WHERE latitude = %s AND longitude = %s AND datetime = %s")
        cursor.execute(query, (latitude, longitude, datetime))
        temperature = cursor.fetchone()[0]
        cursor.close()
        cnx.close()
        return temperature
    except Exception as e:
        return str(e)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    try:
        data = yaml.safe_load(request.data)
        latitude = data['latitude']
        longitude = data['longitude']
        datetime = data['datetime']
        temperature = get_temperature_for_location(latitude, longitude, datetime)
        return jsonify({'temperature': temperature})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()