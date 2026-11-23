import os
import sys
import MySQLdb
from flask import Flask, request, redirect, abort
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    pwd = os.getenv('DB_PASSWORD')
    if not pwd:
        sys.stderr.write('DB_PASSWORD environment variable not set\n')
        abort(500)
    return MySQLdb.connect(host='localhost', user='cwe', passwd=pwd, db='cwe', charset='utf8mb4', use_unicode=True)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    row = None
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password FROM registered_users WHERE username = %s', (username,))
        row = cur.fetchone()
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        return redirect('/internal_server_error')
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    if not row:
        return redirect('/cant_login')
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        return redirect('/success')
    return redirect('/cant_login')

if __name__ == '__main__':
    app.run()