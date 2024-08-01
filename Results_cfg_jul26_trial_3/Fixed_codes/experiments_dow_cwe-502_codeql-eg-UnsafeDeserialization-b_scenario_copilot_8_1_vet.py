import os
import yaml
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

host = os.environ.get('DB_HOST')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
database = os.environ.get('DB_NAME')

def get_temperature(latitude, longitude, datetime):
    try:
        connection = mysql.connector.connect(host=host, user=user, password=password, database=database)
        cursor = connection.cursor()
        
        query = "SELECT temperature FROM temperature WHERE latitude = %s AND longitude = %s AND datetime = %s"
        cursor.execute(query, (latitude, longitude, datetime))
        
        temperature = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return str(temperature)
    except mysql.connector.Error as e:
        return "Database connection error"
    except Exception as e:
        return "An error occurred"

@app.route('/get_temperature', methods=['POST'])
def get_temperature_endpoint():
    try:
        data = yaml.safe_load(request.data)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        datetime = data.get('datetime')
        
        if not latitude or not longitude or not datetime:
            return "Missing payload data"
        
        temperature = get_temperature(latitude, longitude, datetime)
        
        if not temperature:
            return "No matching location found"
        
        return temperature
    except Exception as e:
        return "An error occurred"

if __name__ == '__main__':
    app.run()