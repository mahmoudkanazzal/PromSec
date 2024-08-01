import os
from flask import Flask, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

db = mysql.connector.connect(
    host=os.environ.get('DB_HOST'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    database=os.environ.get('DB_NAME')
)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()

    if user:
        session['username'] = username
        return redirect('/dashboard')
    else:
        return redirect('/login')

if __name__ == '__main__':
    app.run()