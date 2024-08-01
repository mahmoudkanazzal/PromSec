import os
from flask import Flask, request, redirect
import hashlib
import mysql.connector

app = Flask(__name__)

db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'root')
db_password = os.environ.get('DB_PASSWORD', 'password')
db_name = os.environ.get('DB_NAME', 'mydatabase')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def db_connect():
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    hashed_password = hash_password(password)

    db = db_connect()
    cursor = db.cursor()
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, hashed_password))
    user = cursor.fetchone()

    if user:
        db.close()
        return redirect('/')
    else:
        db.close()
        return redirect('/error')

if __name__ == '__main__':
    app.run()