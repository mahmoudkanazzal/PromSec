from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
from werkzeug.security import generate_password_hash

def _get_env(var):
    val = os.getenv(var)
    if val is None:
        raise RuntimeError(f"Missing env var {var}")
    return val

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if not re.fullmatch(r'^[A-Za-z0-9_]{3,30}$', username):
            return 'invalid username', 400
        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password) or not any(not c.isalnum() for c in password):
            return 'invalid password', 400
        hashed = generate_password_hash(password)
        db_host = _get_env('DB_HOST')
        db_user = _get_env('DB_USER')
        db_pass = _get_env('DB_PASS')
        db_name = _get_env('DB_NAME')
        with MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return 'user already exists'
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
                conn.commit()
        return 'register success'
    except Exception as e:
        print(e)
        return 'internal server error', 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)