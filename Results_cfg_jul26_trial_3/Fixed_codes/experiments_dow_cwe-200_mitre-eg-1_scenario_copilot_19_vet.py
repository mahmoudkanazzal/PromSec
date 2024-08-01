import os
from flask import Flask, request, redirect
import mysql.connector
import hashlib

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_DATABASE = os.getenv('DB_DATABASE', 'db')

def connect_to_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    db = connect_to_db()
    cursor = db.cursor()
    
    query = "SELECT password FROM usr WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    
    if result:
        stored_password = result[0]
        if stored_password == hash_password(password):
            return redirect('/success')
    
    return redirect('/wrong')

if __name__ == '__main__':
    app.run()