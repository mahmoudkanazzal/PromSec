import os
from flask import Flask, request
import hashlib
import mysql.connector

app = Flask(__name__)

host = os.environ.get('DB_HOST')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
database = os.environ.get('DB_NAME')

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    cnx = mysql.connector.connect(user=user, password=password, host=host, database=database)
    cursor = cnx.cursor()
    
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, hashed_password))
    
    cnx.commit()
    cursor.close()
    cnx.close()
    
    return 'User registered successfully'

if __name__ == '__main__':
    app.run()