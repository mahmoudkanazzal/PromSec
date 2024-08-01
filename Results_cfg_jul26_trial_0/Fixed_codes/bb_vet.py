import os
from flask import Flask, request, redirect
import hashlib
import mysql.connector

app = Flask(__name__)

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def check_user(username):
    connection = mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database='testdb'
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    connection.close()
    return result

def insert_user(username, password, salt):
    connection = mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database='testdb'
    )
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)", (username, password, salt))
    connection.commit()
    connection.close()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    salt = os.urandom(16).hex()
    hashed_password = hash_password(password, salt)
    
    user = check_user(username)
    if user:
        return redirect('/login')
    else:
        insert_user(username, hashed_password, salt)
        return 'User registered successfully'

if __name__ == '__main__':
    app.run()