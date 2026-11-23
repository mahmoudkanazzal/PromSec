import os
from flask import Flask, request, redirect
import MySQLdb
import bcrypt

db_user = os.getenv('DB_USER', 'root')
db_pass = os.getenv('DB_PASS', '')
db_name = os.getenv('DB_NAME', 'test')
db_host = os.getenv('DB_HOST', 'localhost')

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not isinstance(username, str) or not username:
        return redirect('/wrong')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name, charset='utf8mb4')
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM usr WHERE username=%s LIMIT 1', (username,))
        if cur.fetchone() is None:
            return redirect('/wrong')
        cur.execute('SELECT password_hash FROM usr WHERE username=%s LIMIT 1', (username,))
        row = cur.fetchone()
        if row is None:
            return redirect('/wrong')
        stored_hash = row[0]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password
        if bcrypt.checkpw(password_bytes, stored_hash):
            return redirect('/success')
        else:
            return redirect('/wrong')
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    app.run()