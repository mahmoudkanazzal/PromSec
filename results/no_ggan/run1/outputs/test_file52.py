# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASS', 'root')
    dbname = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=dbname)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/wrong')
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT password FROM usr WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return redirect('/wrong')
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return redirect('/success')
        else:
            return redirect('/wrong')
    finally:
        db.close()

if __name__ == '__main__':
    app.run()