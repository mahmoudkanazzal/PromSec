from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
import secrets

app = Flask(__name__)

USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9]{3,20}$')
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')


def get_db_connection():
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=database)


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not USERNAME_PATTERN.fullmatch(username):
        return redirect('/home')
    if not PASSWORD_PATTERN.fullmatch(password):
        return redirect('/home')
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.sha256(password.encode('utf-8') + salt).digest()
    stored = (pwd_hash + salt).hex()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO user (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, stored))
        conn.commit()
    except MySQLdb.Error:
        print('Database error occurred')
        return redirect('/home')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/home')


if __name__ == '__main__':
    app.run()