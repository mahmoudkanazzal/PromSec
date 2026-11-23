import os, sys
from flask import Flask, request
from werkzeug.security import check_password_hash
import mysql.connector

required_vars = ['DB_HOST', 'DB_USER', 'DB_PASS', 'DB_NAME']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    sys.stderr.write('Missing environment variables: ' + ', '.join(missing_vars) + '\n')
    sys.exit(1)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
DB_SSL_CA = os.getenv('DB_SSL_CA')
FLASK_RUN_HOST = os.getenv('FLASK_RUN_HOST', 'localhost')
FLASK_RUN_PORT = os.getenv('FLASK_RUN_PORT', '5000')
if FLASK_RUN_HOST not in ('127.0.0.1', 'localhost'):
    FLASK_RUN_HOST = '127.0.0.1'

def get_db_connection():
    conn_params = {
        'host': DB_HOST,
        'user': DB_USER,
        'password': DB_PASS,
        'database': DB_NAME,
        'charset': 'utf8mb4'
    }
    if DB_SSL_CA:
        conn_params['ssl_ca'] = DB_SSL_CA
    return mysql.connector.connect(**conn_params)

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT password_hash FROM users WHERE username = %s LIMIT 1', (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            return 'Good Login'
        return 'Bad Login'
    except Exception:
        return 'Bad Login'

if __name__ == '__main__':
    app.run(host=FLASK_RUN_HOST, port=int(FLASK_RUN_PORT), debug=False)