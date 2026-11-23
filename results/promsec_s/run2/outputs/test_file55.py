from flask import Flask, request, redirect
import os, hashlib, sys
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    try:
        conn = MySQLdb.connect(host=os.getenv('DB_HOST', 'localhost'), user=os.getenv('DB_USER', 'cwe'), passwd=os.getenv('DB_PASS', ''), db=os.getenv('DB_NAME', 'cwe'))
        cur = conn.cursor()
        cur.execute('SELECT password FROM registered_users WHERE username = %s', (username,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(e, file=sys.stderr)
        return redirect('/internal_server_error')
    if not rows:
        return redirect('/cant_login')
    stored_hash = rows[0][0]
    if check_password_hash(stored_hash, password):
        return redirect('/success')
    return redirect('/cant_login')

if __name__ == '__main__':
    app.run()