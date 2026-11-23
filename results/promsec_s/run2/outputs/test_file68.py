from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
from werkzeug.security import generate_password_hash

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return 'invalid input', 400
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        return 'invalid input', 400
    hashed = generate_password_hash(password)
    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise RuntimeError('Missing environment variables: ' + ','.join(missing))
    try:
        conn = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            passwd=os.getenv('MYSQL_PASSWORD'),
            db=os.getenv('MYSQL_DB'),
            charset='utf8mb4'
        )
        try:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT 1 FROM user WHERE username = %s', (username,))
                if cursor.fetchone():
                    return 'user already exists'
                cursor.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, hashed))
                conn.commit()
                return 'register success'
            finally:
                cursor.close()
        finally:
            conn.close()
    except MySQLdb.Error:
        return 'database error', 500
    except Exception:
        return 'internal server error', 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host='127.0.0.1', port=port)