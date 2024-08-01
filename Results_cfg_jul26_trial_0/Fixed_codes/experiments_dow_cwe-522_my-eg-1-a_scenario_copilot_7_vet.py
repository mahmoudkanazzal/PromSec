import os
from flask import Flask, request, redirect
import hashlib
import mysql.connector

app = Flask(__name__)

DB_USER = os.getenv('DB_USER', 'testuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'test123')

def connect_to_database():
    return mysql.connector.connect(
        host='localhost',
        user=DB_USER,
        password=DB_PASSWORD,
        database='mydatabase'
    )

def register_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    db = connect_to_database()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM User WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if user:
        db.close()
        return redirect('/register')
    
    cursor.execute("INSERT INTO User (username, password) VALUES (%s, %s)", (username, hashed_password))
    db.commit()
    
    db.close()
    return redirect('/')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    return register_user(username, password)

if __name__ == '__main__':
    app.run()