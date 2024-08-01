import os
from flask import Flask, request, session, redirect
import mysql.connector

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        cnx = mysql.connector.connect(user='root', database='cwe200')
        cursor = cnx.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            return redirect('/session')
        else:
            return 'Incorrect username or password'

    except mysql.connector.Error:
        return 'An error occurred while querying the database'

if __name__ == '__main__':
    app.run()