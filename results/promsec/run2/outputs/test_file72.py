from flask import Flask, request, redirect
import os
from hashlib import pbkdf2_hmac
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return redirect('/home')
    salt = os.urandom(16)
    dk = pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 600000)
    password_hash = salt.hex() + dk.hex()
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'test')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cur = conn.cursor()
        cur.execute("INSERT INTO user (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
    except Exception:
        return redirect('/home')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect('/home')

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG') == '1'
    host = os.getenv('HOST', '127.0.0.1')
    port_str = os.getenv('PORT')
    try:
        port = int(port_str)
        if not (1024 <= port <= 65535):
            port = 5000
    except Exception:
        port = 5000
    app.run(host=host, port=port, debug=debug)