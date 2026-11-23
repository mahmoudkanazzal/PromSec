from flask import Flask, request, redirect
import re, os, bcrypt, MySQLdb, random, string

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    name = request.form['name']
    cweid = request.form['cweid']
    email = request.form['email']
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = MySQLdb.connect(host=os.getenv('DATABASE_URL'), user=os.getenv('DATABASE_USER'), passwd=os.getenv('DATABASE_PASSWORD'), db=os.getenv('DATABASE_NAME'))
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (username, password, name, email, cweid) VALUES (%s, %s, %s, %s, %s)', (username, hashed_pw, name, email, cweid))
        conn.commit()
        user_id = cursor.lastrowid
        session_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
        cursor.execute('INSERT INTO sessions (username, user_id, session_id) VALUES (%s, %s, %s)', (username, user_id, session_id))
        conn.commit()
        cursor.execute('SELECT session_id, stake FROM sessions WHERE user_id = %s AND session_id = %s', (user_id, session_id))
        session = cursor.fetchone()
        conn.close()
        return redirect(f"/login?username={username}&session_id={session[0]}&stake={session[1]}")
    else:
        conn.close()
        return 'Username is already taken'