from flask import Flask, request, redirect
import hashlib
import MySQLdb
import os

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt_hex = salt.hex()
    hash_hex = pwd_hash.hex()
    conn = MySQLdb.connect(host='localhost', user='root', passwd=os.getenv('DB_PASS', ''), db='testdb')
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return redirect('/login', code=307)
    cur.execute(
        "INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, %s)",
        (username, hash_hex, salt_hex, 1)
    )
    conn.commit()
    cur.close()
    conn.close()
    return "Registration successful", 201

if __name__ == '__main__':
    app.run()