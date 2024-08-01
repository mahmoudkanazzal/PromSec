import os
import hashlib
import mysql.connector
from flask import Flask, request

app = Flask(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_user_exists(username):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    return cursor.fetchone() is not None

def add_user_to_db(username, hashed_password):
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    cnx.commit()

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    
    hashed_password = hash_password(password)
    
    if not check_user_exists(username):
        add_user_to_db(username, hashed_password)
        return "User registered successfully!"
    else:
        return "User already exists!"

if __name__ == '__main__':
    cnx = mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )
    cursor = cnx.cursor()
    
    app.run()