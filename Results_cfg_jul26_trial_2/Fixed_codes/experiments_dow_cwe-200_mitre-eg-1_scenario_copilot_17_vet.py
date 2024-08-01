import os
from flask import Flask, request, redirect

app = Flask(__name__)

DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')

def get_user(username):
    # Connect to MySQL database and retrieve user information
    pass

def hash_password(password):
    # Hash password using MD5
    pass

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = get_user(username)

    if user:
        hashed_password = hash_password(password)

        if hashed_password == user['password']:
            return redirect('/user')
        else:
            return 'Incorrect password'
    else:
        return 'User not found'

if __name__ == '__main__':
    app.run()