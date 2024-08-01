import os
import hashlib
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    
    salt = os.urandom(32).hex()
    hashed_password = hash_password(password, salt)
    
    db = MySQLdb.connect("localhost", "username", "password", "database")
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.rowcount > 0:
        return redirect("/login")
    
    cursor.execute("INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)", (username, hashed_password, salt))
    db.commit()
    
    db.close()
    
    return "User registered successfully"

if __name__ == '__main__':
    app.run()