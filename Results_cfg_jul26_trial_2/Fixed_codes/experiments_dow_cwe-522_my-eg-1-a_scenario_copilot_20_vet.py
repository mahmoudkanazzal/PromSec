import os
from flask import Flask, request
import mysql.connector
import hashlib

app = Flask(__name__)

def connect_to_db():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )

def insert_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    insert_user(username, password)
    return 'User registered successfully'

if __name__ == '__main__':
    app.run()