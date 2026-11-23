from __future__ import annotations
import os
import hashlib
from flask import Flask, request, Response
import MySQLdb
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
PASSWORD_SALT = os.getenv('PASSWORD_SALT', '')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, charset='utf8mb4')

def hash_password(pw: str) -> str:
    return hashlib.sha256((PASSWORD_SALT + pw).encode('utf-8')).hexdigest()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return Response('Bad Login', mimetype='text/plain')
    pwd_hash = hash_password(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        sql = "SELECT * FROM user WHERE username=%s AND password=%s"
        cursor.execute(sql, (username, pwd_hash))
        result = cursor.fetchone()
        if result:
            return Response('Good Login', mimetype='text/plain')
        else:
            return Response('Bad Login', mimetype='text/plain')
    except Exception:
        return Response('Bad Login', mimetype='text/plain')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()