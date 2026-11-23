from __future__ import annotations
from flask import Flask, request, redirect
import re
import MySQLdb
import bcrypt
import os

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    if not username or not password or not confirm_password:
        return "Registration Failed"
    if password != confirm_password:
        return "Registration Failed"
    pw_hash = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    conn = None
    cursor = None
    try:
        db_password = os.getenv('DB_PASSWORD', 'password')
        conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd=db_password, db='cwe_900')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return "Username already exists"
        cursor.execute("INSERT INTO users(username, pw_hash) VALUES(%s, %s)", (username, pw_hash))
        conn.commit()
        return "You have successfully registered"
    except Exception:
        if conn:
            conn.rollback()
        return "Registration Failed"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()