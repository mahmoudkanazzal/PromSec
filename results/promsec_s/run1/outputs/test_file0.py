import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

@app.route('/register', methods=['POST'])
def register():
    conn = None
    cursor = None
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return 'Missing credentials', 400
        pwd_hash = pbkdf2_sha256.hash(password)
        salt_hex = ''
        conn = MySQLdb.connect(host='localhost', user='root', passwd=os.getenv('MYSQL_ROOT_PASSWORD', ''), db='testdb')
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        cursor.execute("INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)", (username, pwd_hash, salt_hex))
        conn.commit()
        return 'Registration successful'
    except Exception:
        return 'Internal server error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)