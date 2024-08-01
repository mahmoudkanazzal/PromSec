import os
import yaml
import MySQLdb
from flask import Flask, request

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

def get_temperature_for_location(latitude, longitude, date):
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db='temp_database')
    cursor = conn.cursor()
    query = "SELECT temperature FROM temperatures WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    temperature = cursor.fetchone()[0]
    conn.close()
    return str(temperature)

@app.route('/api/temperature_for_location', methods=['POST'])
def temperature_for_location():
    data = yaml.safe_load(request.data)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    temperature = get_temperature_for_location(latitude, longitude, date)
    return temperature

if __name__ == '__main__':
    app.run()