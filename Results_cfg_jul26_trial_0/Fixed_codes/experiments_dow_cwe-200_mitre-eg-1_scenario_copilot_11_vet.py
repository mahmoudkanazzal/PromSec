import os
import hashlib
import MySQLdb
from flask import Flask, request

app = Flask(__name__)

DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

def login():
    username = request.form['username']
    password = request.form['password']
    
    db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    cursor = db.cursor()
    
    query = "SELECT * FROM users WHERE username=%s AND password=%s"
    cursor.execute(query, (username, hashlib.sha256(password.encode()).hexdigest()))
    
    if cursor.rowcount > 0:
        return "Login successful"
    else:
        return "Login failed"

@app.route('/login', methods=['POST'])
def handle_login():
    return login()

if __name__ == '__main__':
    app.run()