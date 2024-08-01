from flask import Flask, request
import mysql.connector
import os
import hashlib
import secrets

app = Flask(__name__)

db = mysql.connector.connect(
    host=os.environ.get('DB_HOST'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    database=os.environ.get('DB_NAME')
)

cursor = db.cursor()

def generate_salt():
    return secrets.token_hex(16)

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    salt = generate_salt()
    hashed_password = hash_password(password, salt)
    
    sql = "INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)"
    val = (username, hashed_password, salt)
    
    cursor.execute(sql, val)
    db.commit()
    
    return 'User registered successfully'

if __name__ == '__main__':
    app.run()