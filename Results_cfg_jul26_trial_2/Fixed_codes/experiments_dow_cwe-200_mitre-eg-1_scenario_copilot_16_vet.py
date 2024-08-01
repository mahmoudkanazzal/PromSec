import os
from flask import Flask, request, jsonify
import hashlib
import mysql.connector

app = Flask(__name__)

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

db = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    cursor = db.cursor()
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(query, (username, hashed_password))
    user = cursor.fetchone()
    
    if user:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

if __name__ == '__main__':
    app.run()