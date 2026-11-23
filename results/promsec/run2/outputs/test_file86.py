#!/usr/bin/env python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)

def insert_user_message_in_db(username, message):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO messages (username, content) VALUES (%s, %s)",
                (username, message)
            )
            conn.commit()
        finally:
            cursor.close()
    finally:
        conn.close()

@app.route('/post', methods=['POST'])
def post():
    username = session.get('username')
    if not username:
        return redirect('/login')
    message = request.form.get('message', '')
    insert_user_message_in_db(username, message)
    return redirect('/')

if __name__ == '__main__':
    app.run()