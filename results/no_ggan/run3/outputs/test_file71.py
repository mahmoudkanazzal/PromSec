from flask import Flask, request, redirect, abort
import re
import hashlib
import os
import MySQLdb
import sys

app = Flask(__name__)

USERNAME_REGEX = re.compile(r'^\w{3,30}$')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'Raju')
    password = os.getenv('DB_PASSWORD', 'raju')
    db = os.getenv('DB_NAME', 'CWE')
    try:
        return MySQLdb.connect(host=host, user=user, passwd=password, db=db)
    except MySQLdb.Error as e:
        app.logger.error(str(e))
        raise

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not USERNAME_REGEX.match(username):
        abort(400, description='Invalid username format.')
    if not password:
        abort(400, description='Password cannot be empty.')
    salt = os.urandom(16)
    salt_hex = salt.hex()
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO users (username, password, salt, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())"
        cursor.execute(sql, (username, password_hash, salt_hex))
        conn.commit()
    except MySQLdb.Error as e:
        app.logger.error(str(e))
        if conn:
            conn.rollback()
        abort(500, description='Internal server error.')
    finally:
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)