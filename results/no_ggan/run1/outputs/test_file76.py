from flask import Flask, request, redirect, make_response
import os
import bcrypt
import MySQLdb
import random
import string
import urllib.parse

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    name = request.form.get('name', '')
    cweid = request.form.get('cweid', '')
    email = request.form.get('email', '')
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db = MySQLdb.connect(
        host=os.getenv('DATABASE_URL'),
        user=os.getenv('DATABASE_USER'),
        passwd=os.getenv('DATABASE_PASSWORD'),
        db=os.getenv('DATABASE_NAME')
    )
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return 'Username is already taken', 409
    cursor.execute(
        'INSERT INTO users (username, password, name, email, cweid) VALUES (%s, %s, %s, %s, %s)',
        (username, hashed, name, email, cweid)
    )
    db.commit()
    user_id = cursor.lastrowid
    session_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
    cursor.execute(
        'INSERT INTO sessions (username, user_id, session_id) VALUES (%s, %s, %s)',
        (username, user_id, session_id)
    )
    db.commit()
    cursor.execute(
        'SELECT stake FROM sessions WHERE username = %s AND session_id = %s',
        (username, session_id)
    )
    row = cursor.fetchone()
    cursor.close()
    db.close()
    if row:
        stake = row[0]
        query = urllib.parse.urlencode({'username': username, 'session_id': session_id, 'stake': stake})
        resp = make_response(redirect(f'/login?{query}'))
        resp.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='Lax')
        return resp
    return 'Session creation failed', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)