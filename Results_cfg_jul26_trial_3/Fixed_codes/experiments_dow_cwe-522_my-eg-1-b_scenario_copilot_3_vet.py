import os
from flask import Flask, request, jsonify
import hashlib
import uuid

app = Flask(__name__)

def generate_salt():
    return uuid.uuid4().hex

def hash_password(password, salt):
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    salt = generate_salt()
    hashed_password = hash_password(password, salt)

    return jsonify({'message': 'User registered successfully'}), 200

@app.route('/')
def home():
    return 'Welcome to the home page'

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message': 'Page not found'}), 404

if __name__ == '__main__':
    app.run()