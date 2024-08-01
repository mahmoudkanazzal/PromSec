import os
import hashlib
import mysql.connector
from flask import Flask, request

app = Flask(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def connect_to_database():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def check_login(username, password):
    db = connect_to_database()
    cursor = db.cursor()
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, hash_password(password)))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result is not None

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if check_login(username, password):
        return 'Login successful'
    else:
        return 'Login failed'

if __name__ == '__main__':
    app.run()