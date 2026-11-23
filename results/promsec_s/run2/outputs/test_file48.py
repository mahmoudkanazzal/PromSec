import os
import logging
from flask import Flask, request
import mysql.connector
import bcrypt

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'testdb')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        auth_plugin='mysql_native_password'
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT passwort FROM userdaten WHERE username = %s', (username,))
        row = cur.fetchone()
        if row and bcrypt.checkpw(password.encode('utf-8'), row['passwort'].encode('utf-8')):
            return 'Eingeloggt', 200
        return 'Falscher Benutzername oder Passwort', 401
    except mysql.connector.Error as e:
        logging.error(f'Database error: {e}')
        return 'Internal server error', 500
    except Exception as e:
        logging.error(f'Unexpected error: {e}')
        return 'Internal server error', 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port)