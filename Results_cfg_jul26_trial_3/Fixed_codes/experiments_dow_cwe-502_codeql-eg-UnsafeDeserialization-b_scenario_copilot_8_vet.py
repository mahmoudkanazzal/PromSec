import os
import yaml
import mysql.connector

def get_temperature(payload):
    latitude = payload['latitude']
    longitude = payload['longitude']
    date = payload['date']

    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')

    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

    cursor = connection.cursor()
    query = "SELECT temperature FROM temperatures WHERE latitude = %s AND longitude = %s AND date = %s"
    cursor.execute(query, (latitude, longitude, date))
    temperature = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return temperature

# Example usage
with open('payload.yaml', 'r') as file:
    payload = yaml.safe_load(file)

temperature = get_temperature(payload)
print(temperature)