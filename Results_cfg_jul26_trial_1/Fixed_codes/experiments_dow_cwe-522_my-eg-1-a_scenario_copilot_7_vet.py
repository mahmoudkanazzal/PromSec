import os
from flask import Flask, request, redirect

import mysql.connector
from hashlib import sha256

app = Flask(__name__)

def connect_to_database():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'testuser'),
        password=os.getenv('DB_PASSWORD', 'test123'),
        database=os.getenv('DB_DATABASE', 'mydatabase')
    )

def hash_password(password):
    return sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    hashed_password = hash_password(password)
    
    db = connect_to_database()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM User WHERE username = %s", (username,))
    result = cursor.fetchone()
    
    if result:
        return redirect('/register')
    else:
        cursor.execute("INSERT INTO User (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()
        return redirect('/success')

if __name__ == '__main__':
    app.run()