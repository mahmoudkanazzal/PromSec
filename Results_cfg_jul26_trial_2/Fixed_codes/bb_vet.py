import os
import hashlib
import mysql.connector
from flask import Flask, request

app = Flask(__name__)

def generate_salt():
    return os.urandom(16)

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

def check_user_existence(username):
    cnx = mysql.connector.connect(user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                                  host=os.environ.get('DB_HOST'), database=os.environ.get('DB_NAME'))
    cursor = cnx.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    cnx.close()
    return result is not None

def insert_new_user(username, password):
    salt = generate_salt()
    hashed_password = hash_password(password, salt)
    
    cnx = mysql.connector.connect(user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                                  host=os.environ.get('DB_HOST'), database=os.environ.get('DB_NAME'))
    cursor = cnx.cursor()
    query = "INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, hashed_password, salt))
    cnx.commit()
    cursor.close()
    cnx.close()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return 'Username and password are required.', 400
    
    if check_user_existence(username):
        return 'User already exists.', 400
    
    insert_new_user(username, password)
    return 'User registered successfully.', 200

if __name__ == '__main__':
    app.run()