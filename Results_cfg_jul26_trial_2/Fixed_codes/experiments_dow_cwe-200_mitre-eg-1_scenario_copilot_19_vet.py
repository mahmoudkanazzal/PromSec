import os
from flask import Flask, request, redirect
import mysql.connector
import hashlib

app = Flask(__name__)

db_host = os.getenv('DB_HOST', 'localhost')
host = os.getenv('DB_USER', 'root')
passwd = os.getenv('DB_PASS', 'root')
db_name = os.getenv('DB_NAME', 'db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, user_password):
    return hashed_password == hash_password(user_password)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = mysql.connector.connect(host=db_host, user=user, passwd=passwd, db=db_name)
    cursor = conn.cursor()

    query = "SELECT password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result:
        hashed_password = result[0]
        if check_password(hashed_password, password):
            return redirect('/success')
    
    return redirect('/wrong')

if __name__ == '__main__':
    app.run()