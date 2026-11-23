import os, hmac
from flask import Flask, request, redirect
import MySQLdb
from contextlib import closing

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    pwd = os.getenv('DB_PASSWORD', 'r0cknr0l')
    db = os.getenv('DB_NAME', 'cwe200')
    try:
        with closing(MySQLdb.connect(host=host, user=user, passwd=pwd, db=db)) as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                row = cursor.fetchone()
                if row and hmac.compare_digest(str(password), str(row[2])):
                    return redirect(f'/cwe200/{row[0]}')
    except MySQLdb.Error as e:
        print(f'Database error {e.args[0]}')
    return redirect('/cwe200/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)