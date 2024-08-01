import os
import hashlib
import binascii
import mysql.connector
from flask import Flask, request

app = Flask(__name__)

def generate_salt():
    return os.urandom(16)

def hash_password(password, salt):
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(key)

def connect_to_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    salt = generate_salt()
    hashed_password = hash_password(password, salt)
    
    db = connect_to_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)", (username, hashed_password, salt))
    db.commit()
    
    cursor.close()
    db.close()
    
    return 'User registered successfully'

if __name__ == '__main__':
    app.run()