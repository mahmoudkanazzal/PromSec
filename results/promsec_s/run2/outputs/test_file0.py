from flask import Flask, request, redirect
import MySQLdb
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if username is None or password is None:
        return 'Missing fields', 400
    salt = os.urandom(16)
    pwd_hash = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    conn = MySQLdb.connect(host='localhost', user='root', passwd=os.getenv('DB_PASSWORD', ''), db='testdb')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = %s', (username,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return redirect('/login', code=307)
    cursor.execute('INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)', (username, pwd_hash, salt.hex()))
    conn.commit()
    cursor.close()
    conn.close()
    return 'Registration successful'

if __name__ == '__main__':
    app.run(debug=False)