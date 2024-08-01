import os
from flask import Flask, request, redirect
import hashlib
import mysql.connector

app = Flask(__name__)

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    db = mysql.connector.connect(
        host="localhost",
        user=db_user,
        password=db_password,
        database="mydatabase"
    )
    
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM User WHERE username = %s", (username,))
    result = cursor.fetchone()
    
    if result:
        db.close()
        return redirect('/register')
    else:
        cursor.execute("INSERT INTO User (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()
        cursor.close()
        db.close()
        return redirect('/login')

if __name__ == '__main__':
    app.run()
