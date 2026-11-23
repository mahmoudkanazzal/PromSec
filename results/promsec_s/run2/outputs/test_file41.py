from __future__ import print_function
import os
from flask import Flask, request, Response
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return Response('Missing username or password', mimetype='text/plain')
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        return Response('Server configuration error', mimetype='text/plain')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd=db_password, db='cwe_900', charset='utf8mb4')
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return Response('Username already exists', mimetype='text/plain')
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        return Response('You have successfully registered', mimetype='text/plain')
    except Exception:
        if conn:
            conn.rollback()
        return Response('Registration Failed', mimetype='text/plain')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)