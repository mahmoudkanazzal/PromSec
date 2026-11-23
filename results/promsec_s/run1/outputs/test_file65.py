from flask import Flask, request, redirect, make_response
from werkzeug.security import generate_password_hash
import mysql.connector
import os
import re

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not re.fullmatch(r'\w{3,30}', username):
        return make_response('Invalid username', 400)
    if len(password) < 8:
        return make_response('Password too short', 400)
    hashed = generate_password_hash(password)
    db_config = {
        'host': os.getenv('DB_HOST', ''),
        'user': os.getenv('DB_USER', ''),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', '')
    }
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        sql = 'INSERT INTO User (Username, Password, Email) VALUES (%s, %s, %s)'
        cursor.execute(sql, (username, hashed, username))
        conn.commit()
    except mysql.connector.Error:
        return make_response('Database error', 500)
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)