import os
import random
import string
from flask import Flask, request, redirect
import bcrypt
import mysql.connector

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    name = request.form.get('name', '').strip()
    cweid = request.form.get('cweid', '').strip()
    email = request.form.get('email', '').strip()
    if not all([username, password, name, cweid, email]):
        return 'Missing or empty fields', 400
    if len(username) > 150 or not username.isalnum():
        return 'Invalid username', 400
    if len(email) > 150:
        return 'Invalid email', 400
    try:
        db_host = os.getenv('DATABASE_URL')
        db_user = os.getenv('DATABASE_USER')
        db_password = os.getenv('DATABASE_PASSWORD')
        db_name = os.getenv('DATABASE_NAME')
        if not all([db_host, db_user, db_password, db_name]):
            raise RuntimeError('Database configuration missing')
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
    except Exception as e:
        app.logger.error('Database connection error: %s', e)
        return 'Internal server error', 500
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return 'Username is already taken', 409
        pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            'INSERT INTO users (username, password, name, email, cweid) VALUES (%s, %s, %s, %s, %s)',
            (username, pwd_hash, name, email, cweid)
        )
        conn.commit()
        user_id = cursor.lastrowid
        session_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
        cursor.execute(
            'INSERT INTO sessions (username, user_id, session_id) VALUES (%s, %s, %s)',
            (username, user_id, session_id)
        )
        conn.commit()
        cursor.execute('SELECT stake FROM sessions WHERE session_id = %s', (session_id,))
        row = cursor.fetchone()
        stake = row[0] if row else 0
        return redirect(f'/login?username={username}&session_id={session_id}&stake={stake}')
    except Exception as e:
        app.logger.error('Database operation error: %s', e)
        return 'Internal server error', 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run()