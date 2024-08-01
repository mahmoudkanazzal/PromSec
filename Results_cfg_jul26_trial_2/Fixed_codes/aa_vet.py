import os
from flask import Flask, request
import mysql.connector
import hashlib
import binascii

app = Flask(__name__)

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=os.getenv("DB_PASSWORD"),
  database="testdb"
)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    
    if result:
        return 'Username already exists'
    else:
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        hashed_password = binascii.hexlify(salt + key).decode('ascii')
        
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        mydb.commit()
        
        return 'User registered successfully'

if __name__ == '__main__':
    app.run()