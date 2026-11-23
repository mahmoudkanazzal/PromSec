from flask import Flask, request, redirect
import os, hashlib, hmac, MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', 'root')
    db_name = os.getenv('DB_NAME', 'db')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cur = conn.cursor()
        cur.execute('SELECT username, password FROM usr WHERE username = %s', (username,))
        row = cur.fetchone()
        if not row:
            return redirect('/wrong')
        stored_username, stored_password_hash = row
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if stored_username == username and hmac.compare_digest(password_hash, stored_password_hash):
            return redirect('/success')
        else:
            return redirect('/wrong')
    except Exception:
        return redirect('/wrong')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()