import os
from flask import Flask, request, redirect
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'r0cknr0l')
DB_DATABASE = os.getenv('DB_DATABASE', 'cwe200')

def establish_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        db_connection = establish_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            return redirect('/cwe200/' + username)
        else:
            return redirect('/cwe200/')
    except mysql.connector.Error as error:
        print("Error while connecting to MySQL", error)
        return redirect('/cwe200/')
    finally:
        if 'db_connection' in locals():
            cursor.close()
            db_connection.close()

if __name__ == '__main__':
    app.run()