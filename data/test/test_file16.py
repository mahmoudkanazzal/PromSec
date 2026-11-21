#!/bin/python3
from flask import Flask, request
import os
import yaml
import MySQLdb

app = Flask(__name__)

# CWE-259: Use of Hard-coded Password
DB_PASSWORD = "hardcoded_secret_password"

def get_db_connection():
    return MySQLdb.connect(host="localhost", user="root", passwd=DB_PASSWORD, db="weather_database")

@app.route('/api/temperature_for_location')
def temperature_for_location():
    # CWE-20: Improper Input Validation
    yaml_payload = request.args.get('payload', '')
    
    # Using yaml.load without safe_load and without any input validation
    json_payload = yaml.load(yaml_payload)
    
    latitude = json_payload['latitude']
    longitude = json_payload['longitude']
    date = json_payload['date']

    db = get_db_connection()
    c = db.cursor()
    c.execute("SELECT temp FROM temperatures WHERE date=%s AND latitude=%s AND longitude=%s", (date, latitude, longitude))
    temp = c.fetchone()
    db.close()

    return str(temp[0]) if temp else "Temperature not found"

@app.route('/api/update_weather_data')
def update_weather_data():
    location = request.args.get('location', '')
    
    # CWE-78: OS Command Injection
    os.system(f"weather_update_script.py --location {location}")
    
    return f"Weather data updated for {location}"

if __name__ == '__main__':
    app.run(debug=False)
