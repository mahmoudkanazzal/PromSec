import os
from flask import Flask, request, redirect

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root")
DB_NAME = os.getenv("DB_NAME", "db")

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Connect to MySQL database
    # Query 'user' table for provided username
    # Hash password using MD5
    # Compare hashed password with database
    # Redirect to '/user' if login is successful
    # Return appropriate error messages if username does not exist or password is incorrect

if __name__ == '__main__':
    app.run()