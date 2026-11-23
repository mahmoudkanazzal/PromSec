from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
import bcrypt
import random
import string

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    cweid = request.form.get('cweid')
    email = request.form.get('email')
    if not all([username, password, name, cweid, email]):
        return 'Missing fields'
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)
    conn = MySQLdb.connect(
        host=os.getenv('DATABASE_URL'),
        user=os.getenv('DATABASE_USER'),
        passwd=os.getenv('DATABASE_PASSWORD'),
        db=os.getenv('DATABASE_NAME')
    )
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username=%s', (username,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return 'Username is already taken'
    cursor.execute(
        'INSERT INTO users (username, password, name, email, cweid) VALUES (%s, %s, %s, %s, %s)',
        (username, hashed_pw, name, email, cweid)
    )
    conn.commit()
    session_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
    cursor.execute(
        'SELECT session_id, stake FROM sessions WHERE username=%s AND session_id=%s',
        (username, session_id)
    )
    row = cursor.fetchone()
    if row:
        session_id, stake = row[0], row[1]
    else:
        stake = 0
    cursor.close()
    conn.close()
    return redirect(f'/login?username={username}&session_id={session_id}&stake={stake}')

if __name__ == '__main__':
    app.run()