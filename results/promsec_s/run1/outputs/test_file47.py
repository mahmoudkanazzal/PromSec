from flask import Flask, request, redirect
import os, hashlib, MySQLdb

def const_eq(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASSWORD', 'root')
    db = os.getenv('DB_NAME', 'db')
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)
        cur = conn.cursor()
        cur.execute('SELECT * FROM user WHERE username=%s', (username,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        return 'Login failed!'
    if not rows:
        return 'Login failed!'
    stored_hash = rows[0][1]
    supplied_hash = hashlib.sha1(password.encode()).hexdigest()
    if const_eq(stored_hash, supplied_hash):
        return 'Welcome ' + username + '!'
    return 'Login failed!'

if __name__ == '__main__':
    app.run()