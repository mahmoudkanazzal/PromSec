import os
from flask import Flask, request, redirect
import hashlib
import mysql.connector

app = Flask(__name__)

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def check_user(username):
    cnx = mysql.connector.connect(user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                                  host='localhost', database='testdb')
    cursor = cnx.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    cnx.close()
    return result

def insert_user(username, password, salt):
    cnx = mysql.connector.connect(user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'),
                                  host='localhost', database='testdb')
    cursor = cnx.cursor()
    query = "INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, password, salt))
    cnx.commit()
    cursor.close()
    cnx.close()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = check_user(username)
    if user:
        return redirect('/login')
    else:
        salt = os.urandom(16).hex()
        hashed_password = hash_password(password, salt)
        insert_user(username, hashed_password, salt)
        return 'User registered successfully'

if __name__ == '__main__':
    app.run()