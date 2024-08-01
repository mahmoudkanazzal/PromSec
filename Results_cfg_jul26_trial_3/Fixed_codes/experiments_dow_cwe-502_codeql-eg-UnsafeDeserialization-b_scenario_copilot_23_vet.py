import os
from flask import Flask, request, jsonify
import yaml
import mysql.connector

app = Flask(__name__)

def get_min_temperature(latitude, longitude, date):
    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database='your_database_name'
    )
    
    cursor = connection.cursor()
    query = "SELECT MIN(temperature) FROM temperatures WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    min_temperature = cursor.fetchone()[0]
    
    cursor.close()
    connection.close()
    
    return min_temperature

@app.route('/get_min_temperature', methods=['POST'])
def get_min_temperature_endpoint():
    data = yaml.safe_load(request.data)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    
    min_temperature = get_min_temperature(latitude, longitude, date)
    
    return jsonify({'min_temperature': min_temperature})

if __name__ == '__main__':
    app.run()
