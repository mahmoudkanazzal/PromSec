import os, logging, hmac, hashlib
from flask import Flask, request, redirect
import MySQLdb

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', 'r0cknr0l')
    db_name = os.getenv('DB_NAME', 'cwe200')
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
    except MySQLdb.Error as e:
        logging.error('Database connection error: %s', e)
        return ('Internal Server Error', 500)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return redirect('/cwe200/')
        stored_username = row[0]
        stored_hash = row[2]
        computed_hash = hashlib.sha256(password.encode()).hexdigest()
        if hmac.compare_digest(computed_hash, stored_hash):
            return redirect(f'/cwe200/{stored_username}')
        else:
            return redirect('/cwe200/')
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)