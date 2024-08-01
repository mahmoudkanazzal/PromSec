import os
from flask import Flask, request, redirect
import mysql.connector
import hashlib

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'r0cknr0l')
DB_NAME = os.getenv('DB_NAME', 'cwe200')

def connect_to_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASS,
        db=DB_NAME
    )

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form['username']
        password = request.form['password']

        db = connect_to_db()
        cursor = db.cursor()

        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if user:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if user[2] == hashed_password:
                return redirect("/cwe200/" + username)
        
        return redirect("/cwe200/")
    
    except mysql.connector.Error as err:
        print("MySQL error: {}".format(err))
        return redirect("/cwe200/")
    
    finally:
        cursor.close()
        db.close()

if __name__ == '__main__':
    app.run()