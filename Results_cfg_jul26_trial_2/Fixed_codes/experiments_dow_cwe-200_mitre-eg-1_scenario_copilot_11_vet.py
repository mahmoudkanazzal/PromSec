import os
from flask import Flask, request, jsonify
import hashlib
import mysql.connector

app = Flask(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    hashed_password = hash_password(password)
    # Connect to MySQL database
    cnx = mysql.connector.connect(user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                                  host=os.environ.get('DB_HOST'), database=os.environ.get('DB_NAME'))
    cursor = cnx.cursor()
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, hashed_password))
    result = cursor.fetchone()
    cursor.close()
    cnx.close()
    return result is not None

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if verify_user(username, password):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

if __name__ == '__main__':
    app.run()