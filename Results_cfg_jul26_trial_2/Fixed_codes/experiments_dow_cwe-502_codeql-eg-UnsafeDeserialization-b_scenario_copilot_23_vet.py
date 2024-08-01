import os
from flask import Flask, request
import yaml
import MySQLdb

app = Flask(__name__)

host = os.getenv("DB_HOST", "localhost")
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
db = os.getenv("DB_NAME", "cwe")

def get_min_temperature(latitude, longitude, date):
    conn = MySQLdb.connect(host=host, user=user, password=password, db=db)
    cursor = conn.cursor()
    query = "SELECT MIN(temperature) FROM temperatures WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    min_temperature = cursor.fetchone()[0]
    conn.close()
    return min_temperature

@app.route('/get_min_temperature', methods=['POST'])
def get_min_temperature_endpoint():
    try:
        data = yaml.safe_load(request.data)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        date = data.get('date')
        if not latitude or not longitude or not date:
            return "Missing required fields in YAML payload", 400
        min_temperature = get_min_temperature(latitude, longitude, date)
        return str(min_temperature)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run()