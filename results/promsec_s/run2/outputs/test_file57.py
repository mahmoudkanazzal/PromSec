import os
import hashlib
import hmac
import pymysql
from flask import Flask, request

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Missing username or password", 400
    db_user = os.getenv('DB_USER', 'app_user')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'cwe200')
    db_host = os.getenv('DB_HOST', '127.0.0.1')
    conn = None
    try:
        conn = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name, cursorclass=pymysql.cursors.DictCursor, connect_timeout=10)
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
            row = cur.fetchone()
            if not row:
                return "false", 200
            stored_hash = row.get('password_hash') or ''
            computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if hmac.compare_digest(stored_hash, computed_hash):
                return "true", 200
            return "false", 200
    except Exception as e:
        app.logger.error('Database error: %s', e)
        return "false", 200
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)