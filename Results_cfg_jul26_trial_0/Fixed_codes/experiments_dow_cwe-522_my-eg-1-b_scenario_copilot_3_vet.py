import os
from flask import Flask, request, redirect

import hashlib
import mysql.connector

app = Flask(__name__)

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

@app.route('/register', methods=['POST'])
def register_user():
    try:
        username = request.form['username']
        password = request.form['password']
        
        salt = os.environ.get('SALT')
        hashed_password = hash_password(password, salt)
        
        db = mysql.connector.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME')
        )
        
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()
        
        return redirect('/home')
    except Exception as e:
        return redirect('/home')

if __name__ == '__main__':
    app.run()