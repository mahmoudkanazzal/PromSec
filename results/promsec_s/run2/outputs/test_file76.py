from flask import Flask, request, redirect
import os
import bcrypt
import random
import string
import MySQLdb
from urllib.parse import urlencode

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DATABASE_URL')
    user = os.getenv('DATABASE_USER')
    password = os.getenv('DATABASE_PASSWORD')
    db = os.getenv('DATABASE_NAME')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

def generate_session_id():
    rng = random.SystemRandom()
    chars = string.ascii_uppercase + string.digits
    return ''.join(rng.choice(chars) for _ in range(16))

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    name = request.form.get('name', '')
    cweid = request.form.get('cweid', '')
    email = request.form.get('email', '')
    if not username or not password:
        return 'Missing username or password', 400
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username=%s', (username,))
        if cur.fetchone():
            return 'Username already taken', 200
        cur.execute('INSERT INTO users (username,password,name,email,cweid) VALUES (%s,%s,%s,%s,%s)', (username, hashed_pw, name, email, cweid))
        conn.commit()
        user_id = cur.lastrowid
        session_id = generate_session_id()
        cur.execute('SELECT session_id, stake FROM sessions WHERE username=%s AND session_id=%s', (username, session_id))
        row = cur.fetchone()
        if row:
            sess_id, stake = row
        else:
            stake = 0
            sess_id = session_id
        query = urlencode({'username': username, 'session_id': sess_id, 'stake': stake})
        return redirect(f'/login?{query}')
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run()