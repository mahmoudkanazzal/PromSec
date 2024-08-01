import os
from flask import Flask, request
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host=os.environ.get('DB_HOST'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASS'),
    database=os.environ.get('DB_NAME')
)

def hash_password(password):
    return generate_password_hash(password)

def check_credentials(username, password):
    cursor = db.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    if result:
        return check_password_hash(result[0], password)
    return False

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        return {'message': 'Missing username or password'}, 400
    
    if check_credentials(username, password):
        return {'message': 'Login successful'}, 200
    else:
        return {'message': 'Invalid credentials'}, 401

if __name__ == '__main__':
    app.run()