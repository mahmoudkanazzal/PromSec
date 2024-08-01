import os
from flask import Flask, request
import yaml
import mysql.connector

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['POST'])
def get_temperature_for_location():
    data = yaml.safe_load(request.data)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')

    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'root')
    db_database = os.environ.get('DB_DATABASE', 'temp_database')

    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )
    cursor = connection.cursor()

    query = "SELECT temperature FROM temperatures WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    temperature = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return str(temperature)

if __name__ == '__main__':
    app.run()