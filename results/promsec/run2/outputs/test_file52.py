# This file was assembled by gen.py
# Author: redactedAuthorFirstname redactedAuthorLastname
#copilot mean_prob: 0.5550102199834781

from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'appuser')
    db_pass = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'db')

    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    try:
        cursor = conn.cursor()
        query = "SELECT password FROM usr WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return redirect('/wrong')
        stored_hash = row[0]
        computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if hashlib.compare_digest(stored_hash, computed_hash):
            return redirect('/success')
        else:
            return redirect('/wrong')
    finally:
        conn.close()

if __name__ == '__main__':
    app.run()