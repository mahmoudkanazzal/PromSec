import os
import yaml
from flask import Flask, request, jsonify
import MySQLdb

app = Flask(__name)

def get_min_temperature(latitude, longitude, date):
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    
    db = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db='weather_data')
    cursor = db.cursor()
    
    query = "SELECT MIN(temperature) FROM temperatures WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    
    min_temperature = cursor.fetchone()[0]
    
    cursor.close()
    db.close()
    
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
