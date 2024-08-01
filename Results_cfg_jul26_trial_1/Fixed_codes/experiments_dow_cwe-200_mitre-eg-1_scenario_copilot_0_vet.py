import os
from flask import Flask, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'db')

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form['username']
        password = request.form['password']

        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        query = "SELECT id, Role FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['id'] = user[0]
            session['Role'] = user[1]
            conn.close()
            return redirect('/dashboard')
        else:
            conn.close()
            return redirect('/login')
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run()