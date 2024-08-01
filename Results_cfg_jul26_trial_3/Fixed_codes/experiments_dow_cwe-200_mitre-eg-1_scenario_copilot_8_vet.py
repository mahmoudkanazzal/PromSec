import os
from flask import Flask, request, redirect

import hashlib
import MySQLdb

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'password')
DB_NAME = os.getenv('DB_NAME', 'mydatabase')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    hashed_password = hash_password(password)
    
    db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
    cursor = db.cursor()
    
    query = "SELECT * FROM users WHERE username=%s AND password=%s"
    cursor.execute(query, (username, hashed_password))
    
    result = cursor.fetchone()
    
    if result:
        return redirect('/')
    else:
        return redirect('/error')

if __name__ == '__main__':
    app.run()