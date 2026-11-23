from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
import secrets

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing credentials', 400
    salt = secrets.token_bytes(16)
    hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    db = MySQLdb.connect(host='localhost', user='root', passwd=os.getenv('DB_PASSWORD', ''), db='testdb')
    cursor = db.cursor()
    cursor.execute('SELECT username FROM users WHERE username = %s', (username,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return redirect('/login', code=307)
    cursor.execute('INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, %s)', (username, hashed_password, salt, 1))
    db.commit()
    cursor.close()
    db.close()
    return 'Registration successful', 200

if __name__ == '__main__':
    app.run()