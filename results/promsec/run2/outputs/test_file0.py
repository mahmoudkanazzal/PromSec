from flask import Flask, request, redirect
import MySQLdb
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    salt = os.urandom(16)
    password_hash = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    conn = MySQLdb.connect(host='localhost', user='root', passwd=os.getenv('DB_PASS', ''), db='testdb')
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return redirect('/login', code=307)
    cur.execute('INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)', (username, password_hash, salt.hex()))
    conn.commit()
    cur.close()
    conn.close()
    return 'Registration successful', 200

if __name__ == '__main__':
    app.run(debug=False)