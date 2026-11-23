import os
from flask import Flask, request, Response
import MySQLdb
import bcrypt

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'test')

def get_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').encode('utf-8')
    if not username or not password:
        return Response('Login failed!', mimetype='text/plain'), 401
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM user WHERE username=%s', (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row is None:
            return Response('Login failed!', mimetype='text/plain'), 401
        stored_hash = row[0].encode('utf-8')
        if bcrypt.checkpw(password, stored_hash):
            return Response(f'Welcome {username}!', mimetype='text/plain'), 200
        else:
            return Response('Login failed!', mimetype='text/plain'), 401
    except Exception:
        return Response('Login failed!', mimetype='text/plain'), 401

if __name__ == '__main__':
    app.run()