import os
from flask import Flask, request, jsonify
import mysql.connector
import hashlib

app = Flask(__name__)

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = "mysql.eecs.oregonstate.edu"
DB_NAME = "your_database_name"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_existing_user(username):
    conn = mysql.connector.connect(user=DB_USERNAME, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    conn.close()
    return result

def insert_new_user(username, password):
    conn = mysql.connector.connect(user=DB_USERNAME, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400

    username = data['username']
    password = data['password']

    if check_existing_user(username):
        return jsonify({"error": "Username already exists"}), 400

    insert_new_user(username, password)
    return jsonify({"message": "User registered successfully"}), 200

if __name__ == '__main__':
    app.run()