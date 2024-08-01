from flask import Flask, request, jsonify
import yaml
import pymysql
import os

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_temperature(latitude, longitude, datetime):
    connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = connection.cursor()
    query = "SELECT temperature FROM temperatures WHERE latitude = %s AND longitude = %s AND datetime = %s"
    cursor.execute(query, (latitude, longitude, datetime))
    temperature = cursor.fetchone()[0]
    connection.close()
    return temperature

@app.route('/get_temperature', methods=['POST'])
def get_temperature_endpoint():
    data = yaml.safe_load(request.data)
    latitude = data['latitude']
    longitude = data['longitude']
    datetime = data['datetime']
    temperature = get_temperature(latitude, longitude, datetime)
    return jsonify({'temperature': temperature})

if __name__ == '__main__':
    app.run()