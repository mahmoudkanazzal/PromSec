import os
from flask import Flask, request
import hashlib
import mysql.connector

app = Flask(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_user(username):
    cnx = mysql.connector.connect(user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                                  host=os.environ.get('DB_HOST'), database=os.environ.get('DB_NAME'))
    cursor = cnx.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    cnx.close()
    return result

def insert_user(username, password):
    cnx = mysql.connector.connect(user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                                  host=os.environ.get('DB_HOST'), database=os.environ.get('DB_NAME'))
    cursor = cnx.cursor()
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, hash_password(password)))
    cnx.commit()
    cursor.close()
    cnx.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if check_user(username):
        return 'User already exists', 400
    else:
        insert_user(username, password)
        return 'User registered successfully', 200

if __name__ == '__main__':
    app.run()