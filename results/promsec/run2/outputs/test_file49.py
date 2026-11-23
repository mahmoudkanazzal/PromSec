from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'test')
    conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4', use_unicode=True)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s AND pass=%s", (username, password))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return redirect('/dashboard')
    else:
        return redirect('/')

if __name__ == '__main__':
    app.run()