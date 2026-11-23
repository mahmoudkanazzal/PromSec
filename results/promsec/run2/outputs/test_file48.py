import os
from flask import Flask, request, redirect
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'test')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cur = conn.cursor()
        cur.execute("SELECT passwort FROM userdaten WHERE username = %s", (username,))
        row = cur.fetchone()
        if row and check_password_hash(row[0], password):
            return 'Eingeloggt'
        return 'Falscher Benutzername oder Passwort'
    except Exception:
        return 'Falscher Benutzername oder Passwort'
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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)