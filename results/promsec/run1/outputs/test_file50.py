from flask import Flask, request
import os, hashlib, MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    passwd = os.getenv('DB_PASS', '')
    dbname = os.getenv('DB_NAME', 'db')
    conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=dbname)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM user WHERE username = %s', (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "Wrong Username"
    stored_hash = row[0]
    supplied_hash = hashlib.sha256(password.encode()).hexdigest()
    if hashlib.compare_digest(stored_hash, supplied_hash):
        return "Login Success"
    return "Wrong Password"

if __name__ == '__main__':
    app.run()