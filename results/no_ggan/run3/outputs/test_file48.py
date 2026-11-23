from flask import Flask, request, redirect
import os, sys, hashlib
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Benutzername und Passwort erforderlich', 400
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'db')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name, charset='utf8mb4')
        cur = conn.cursor()
        cur.execute("SELECT passwort FROM userdaten WHERE username=%s", (username,))
        row = cur.fetchone()
        if row and check_password_hash(row[0], password):
            return 'Eingeloggt'
        return 'Falscher Benutzername oder Passwort', 401
    except MySQLdb.Error as e:
        sys.stderr.write(f'Database error: {e}\n')
        return 'Interner Serverfehler', 500
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    app.run()