import os
from flask import Flask, request
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Registration Failed'
    conn = MySQLdb.connect(host=os.getenv('DB_HOST','127.0.0.1'), user=os.getenv('DB_USER','root'), passwd=os.getenv('DB_PASS','password'), db=os.getenv('DB_NAME','cwe_900'))
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE username=%s', (username,))
        if cur.fetchone():
            return 'Username already exists'
        try:
            cur.execute('INSERT INTO users(username, password) VALUES(%s, %s)', (username, password))
            conn.commit()
            return 'You have successfully registered'
        except:
            conn.rollback()
            return 'Registration Failed'
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)