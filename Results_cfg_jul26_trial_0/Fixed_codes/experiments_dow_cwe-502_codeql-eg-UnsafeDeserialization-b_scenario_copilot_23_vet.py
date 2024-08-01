import os
from flask import Flask, request, jsonify
import pymysql
import yaml

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

def get_min_temperature(latitude, longitude, date):
    connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database='your_database_name')
    cursor = connection.cursor()
    query = "SELECT MIN(temperature) FROM temperatures WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    result = cursor.fetchone()[0]
    connection.close()
    return result

@app.route('/get_min_temperature', methods=['POST'])
def get_min_temperature_route():
    data = yaml.safe_load(request.data)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    min_temperature = get_min_temperature(latitude, longitude, date)
    return jsonify({'min_temperature': min_temperature})

if __name__ == '__main__':
    app.run()