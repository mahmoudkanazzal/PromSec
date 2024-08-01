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

    try:
        db = connect_to_db()
        cursor = db.cursor()

        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        hashed_password = hash_password(password)
        cursor.execute(query, (username, hashed_password))
        user = cursor.fetchone()

        if user:
            return redirect('/success')
        else:
            return redirect('/wrong')

    except mysql.connector.Error as err:
        return "An error occurred"

    finally:
        cursor.close()
        db.close()

if __name__ == '__main__':
    app.run()