import os
from flask import Flask, request, redirect

import MySQLdb

app = Flask(__name__)

db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'root')
db_password = os.environ.get('DB_PASSWORD', 'cisco123')
db_name = os.environ.get('DB_NAME', 'mysite')

db = MySQLdb.connect(host=db_host, user=db_user, password=db_password, db=db_name)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    db.commit()
    
    return redirect('/home')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    
    if user:
        return redirect('/dashboard')
    else:
        return "Invalid credentials"

if __name__ == '__main__':
    app.run()