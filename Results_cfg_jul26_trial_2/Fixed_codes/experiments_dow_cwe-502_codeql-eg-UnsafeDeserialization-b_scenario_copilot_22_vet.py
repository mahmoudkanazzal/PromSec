import os
from flask import Flask, request
import yaml
import pymysql

app = Flask(__name__)

@app.route('/api/temperature_for_location')
def get_temperature_for_location():
    try:
        payload = request.args.get('payload')
        data = yaml.safe_load(payload)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        date = data.get('date')

        db = pymysql.connect(host='localhost', user='root', password=os.environ.get('MYSQL_PASSWORD'), database='cwe_db')
        cursor = db.cursor()
        query = "SELECT temperature FROM temperature_data WHERE latitude = %s AND longitude = %s AND date = %s"
        cursor.execute(query, (latitude, longitude, date))
        temperature = cursor.fetchone()[0]

        db.close()
        return str(temperature)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run()