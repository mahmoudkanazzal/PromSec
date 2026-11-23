import os
import re
from pathlib import Path
from flask import Flask, request, redirect, make_response, jsonify
import mysql.connector
from passlib.hash import bcrypt
from dotenv import load_dotenv

if Path('.env').exists():
    load_dotenv(override=False)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False
    )

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_]{3,30}$')

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not USERNAME_REGEX.match(username):
        return jsonify({'error': 'Invalid username'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return redirect('./register')
        password_hash = bcrypt.hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
        conn.commit()
        return redirect('./login')
    except Exception:
        if conn:
            conn.rollback()
        return make_response('Internal server error', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)