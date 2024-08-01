import os
from flask import Flask, request, redirect
import hashlib
import mysql.connector

app = Flask(__name__)

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_username_exists(username):
    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    conn.close()
    return result

def insert_user(username, password):
    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    hashed_password = hash_password(password)
    
    if check_username_exists(username):
        return redirect('/registration_page')
    else:
        insert_user(username, hashed_password)
        return redirect('/success_page')

if __name__ == '__main__':
    app.run()