#!/bin/python3
import os
from flask import Flask, request, redirect
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'cwe'),
            passwd=os.getenv('DB_PASS', 'password'),
            db=os.getenv('DB_NAME', 'cwe')
        )
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM registered_users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if row is None:
            return redirect('/cant_login')
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return redirect('/success')
        else:
            return redirect('/cant_login')
    except Exception as e:
        app.logger.error(e)
        return redirect('/internal_server_error')
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

if __name__ == '__main__':
    app.run()