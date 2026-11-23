import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect, make_response

app = Flask(__name__)

secret = os.getenv('FLASK_SECRET_KEY')
if secret:
    app.secret_key = secret
else:
    app.secret_key = os.urandom(24)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return make_response('Missing username or password', 400)
    salt_bytes = os.urandom(16)
    salt_hex = salt_bytes.hex()
    password_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME', 'testdb')
    if not db_password:
        return make_response('Database password not configured', 500)
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name, charset='utf8mb4', use_unicode=True)
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username=%s LIMIT 1', (username,))
        if cur.fetchone():
            return redirect('/login', code=307)
        cur.execute('INSERT INTO users (username, password_hash, salt, created_at) VALUES (%s, %s, %s, UNIX_TIMESTAMP())', (username, password_hash, salt_hex))
        conn.commit()
        return make_response('User registered successfully', 201)
    except Exception as e:
        return make_response(str(e), 500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)