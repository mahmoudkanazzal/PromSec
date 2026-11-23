from __future__ import annotations
import os
import re
import logging
from flask import Flask, request, jsonify
import mysql.connector
import bcrypt

# Flask registration endpoint with secure handling
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_]{3,30}$')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False,
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not USERNAME_REGEX.fullmatch(username):
        return jsonify({'error': 'Invalid username format'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM users WHERE username = %s",
                    (username,)
                )
                if cursor.fetchone():
                    return jsonify({'error': 'Username already taken'}), 409

                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, hashed_pw)
                )
                conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except mysql.connector.Error as db_err:
        logging.exception("Database error during registration")
        try:
            if conn.is_connected():
                conn.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Registration Failed'}), 500
    except Exception:
        logging.exception("Unexpected error during registration")
        return jsonify({'error': 'Registration Failed'}), 500
    finally:
        try:
            if conn.is_connected():
                conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)