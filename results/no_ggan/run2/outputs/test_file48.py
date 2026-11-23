# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
import os
import hashlib
import MySQLdb

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('MYSQL_HOST', 'localhost')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', 'root')
    db = os.getenv('MYSQL_DB', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    pwd_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM userdaten WHERE username=%s AND passwort=%s"
        cursor.execute(query, (username, pwd_hash))
        result = cursor.fetchone()
    finally:
        if conn:
            conn.close()
    if result:
        return "Eingeloggt"
    else:
        return "Falscher Benutzername oder Passwort"

if __name__ == '__main__':
    app.run()