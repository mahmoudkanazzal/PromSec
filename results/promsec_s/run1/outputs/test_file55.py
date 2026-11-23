from flask import Flask, request, redirect
import os
import sys
import hashlib
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'cwe')
    passwd = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'cwe')
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM registered_users WHERE username=%s", (username,))
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(e, file=sys.stderr)
        return redirect('/internal_server_error')
    if not rows:
        return redirect('/cant_login')
    stored_hash = rows[0][0]
    supplied_hash = hashlib.sha1(password.encode('utf-8')).hexdigest()
    if supplied_hash == stored_hash:
        return redirect('/success')
    else:
        return redirect('/cant_login')

if __name__ == '__main__':
    app.run()