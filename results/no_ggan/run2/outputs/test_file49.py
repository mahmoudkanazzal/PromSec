from flask import Flask, request, redirect
import os, hashlib, MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'db')
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND pass=%s", (username, pwd_hash))
        result = cur.fetchone()
        if result:
            return redirect('/dashboard')
        else:
            return redirect('/')
    finally:
        conn.close()

if __name__ == '__main__':
    app.run()