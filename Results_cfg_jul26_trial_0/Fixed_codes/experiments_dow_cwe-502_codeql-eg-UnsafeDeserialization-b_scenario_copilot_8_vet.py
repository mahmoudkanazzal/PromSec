import os
from flask import Flask, request, jsonify
import pymysql
import yaml

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = 'weather_db'

def get_temperature(latitude, longitude, datetime):
    try:
        connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = connection.cursor()
        
        query = "SELECT temperature FROM weather_data WHERE latitude = %s AND longitude = %s AND datetime = %s"
        cursor.execute(query, (latitude, longitude, datetime))
        
        temperature = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return temperature
    except Exception as e:
        return str(e)

@app.route('/get_temperature', methods=['POST'])
def get_temperature_endpoint():
    data = yaml.safe_load(request.data)
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    datetime = data.get('datetime')
    
    temperature = get_temperature(latitude, longitude, datetime)
    
    return jsonify({'temperature': temperature})

if __name__ == '__main__':
    app.run()