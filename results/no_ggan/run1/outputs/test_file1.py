import os
import re
import hashlib
from datetime import datetime
from flask import Flask, request, abort, Response
import MySQLdb
import MySQLdb.cursors

USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_]{3,30}$')
PASSWORD_MIN_LENGTH = 8

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    db = os.getenv('DB_NAME')
    if not user or not password or not db:
        raise RuntimeError('Database configuration missing')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', cursorclass=MySQLdb.cursors.DictCursor, autocommit=False)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        abort(400)
    if not USERNAME_PATTERN.match(username):
        abort(400)
    if len(password) < PASSWORD_MIN_LENGTH:
        abort(400)
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000).hex()
    salt_hex = salt.hex()
    created = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s LIMIT 1', (username,))
        if cursor.fetchone():
            abort(409)
        cursor.execute('INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, %s)', (username, pwd_hash, salt_hex, created))
        conn.commit()
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        abort(500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return Response('Registration successful', status=201, mimetype='text/plain')

if __name__ == '__main__':
    app.run()