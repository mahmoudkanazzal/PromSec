from flask import Flask, request, redirect
import os, hashlib, hmac, MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'db')
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        stored_hash = row[1]
        supplied_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if hmac.compare_digest(supplied_hash, stored_hash):
            return "success"
        else:
            return "wrong pw"
    else:
        return "username not found"

if __name__ == '__main__':
    app.run()