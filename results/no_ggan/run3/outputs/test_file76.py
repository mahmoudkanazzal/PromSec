from flask import Flask, request, redirect, make_response
import re
import hashlib
import MySQLdb
import os
import bcrypt
import random
import string
import urllib.parse

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    name = request.form.get('name', '')
    cweid = request.form.get('cweid', '')
    email = request.form.get('email', '')
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db = MySQLdb.connect(
        host=os.getenv('DATABASE_URL', ''),
        user=os.getenv('DATABASE_USER', ''),
        passwd=os.getenv('DATABASE_PASSWORD', ''),
        db=os.getenv('DATABASE_NAME', '')
    )
    try:
        cursor = db.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            return 'Username is already taken'
        cursor.execute(
            'INSERT INTO users (username, password, name, email, cweid) VALUES (%s, %s, %s, %s, %s)',
            (username, hashed_pw, name, email, cweid)
        )
        db.commit()
        user_id = cursor.lastrowid
        rng = random.SystemRandom()
        session_id = ''.join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        cursor.execute(
            'INSERT INTO sessions (username, user_id, session_id) VALUES (%s, %s, %s)',
            (username, user_id, session_id)
        )
        db.commit()
        cursor.execute(
            'SELECT username, password, session_id, stake FROM sessions WHERE session_id=%s',
            (session_id,)
        )
        row = cursor.fetchone()
        if row:
            uname, pw, sid, stake = row
            query = urllib.parse.urlencode({
                'username': uname,
                'session_id': sid,
                'stake': stake if stake is not None else ''
            })
            resp = make_response(redirect(f'/login?{query}'))
            resp.set_cookie('session_id', session_id, httponly=True, secure=True)
            return resp
        else:
            return 'Session creation failed', 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run()