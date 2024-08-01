import os
from flask import Flask, request
import hashlib

app = Flask(__name__)

stored_password = os.getenv('HASHED_PASSWORD')

@app.route('/login', methods=['POST'])
def login():
    input_password = request.form['password']
    hashed_input_password = hashlib.sha256(input_password.encode()).hexdigest()
    
    if hashed_input_password == stored_password:
        return 'Welcome {username}!'
    else:
        return 'Login failed'

if __name__ == '__main__':
    app.run()