import os
import re
import bcrypt
from flask import Flask, request
import MySQLdb

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_secret')
MYSQL_USER = os.getenv('MYSQL_USER', 'app_user')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
if not MYSQL_PASSWORD:
    raise RuntimeError('MYSQL_PASSWORD environment variable is required')
MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'cwe_900')
MYSQL_SSL_CA = os.getenv('MYSQL_SSL_CA')

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    if not re.fullmatch(r'\w{3,30}', username):
        return 'Invalid username'
    if password != confirm_password:
        return 'Passwords do not match'
    if len(password) < 8:
        return 'Password must be at least 8 characters long'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    ssl_params = {'ca': MYSQL_SSL_CA} if MYSQL_SSL_CA else None
    conn = None
    try:
        conn = MySQLdb.connect(user=MYSQL_USER, passwd=MYSQL_PASSWORD, host=MYSQL_HOST, db=MYSQL_DATABASE, charset='utf8mb4', autocommit=False, ssl=ssl_params)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return 'Username already exists'
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
        conn.commit()
        return 'You have successfully registered'
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return 'Registration Failed'
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)