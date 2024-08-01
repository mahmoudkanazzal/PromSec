import os
import hashlib
import mysql.connector
from flask import Flask, request

app = Flask(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def connect_to_database():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    db = connect_to_database()
    cursor = db.cursor()
    
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, hash_password(password)))
    
    user = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if user:
        return "Login successful"
    else:
        return "Login failed"

if __name__ == '__main__':
    app.run()