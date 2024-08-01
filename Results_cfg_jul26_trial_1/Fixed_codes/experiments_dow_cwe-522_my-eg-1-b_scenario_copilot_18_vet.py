import os
import hashlib
import binascii
import mysql.connector
from flask import Flask, redirect, request

app = Flask(__name__)

def hash_password(password, salt):
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(key)

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    
    salt = os.urandom(32)
    hashed_password = hash_password(password, salt)
    
    db = mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )
    cursor = db.cursor()
    
    query = "INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, hashed_password, salt))
    
    db.commit()
    db.close()
    
    return redirect('/main')

if __name__ == '__main__':
    app.run()