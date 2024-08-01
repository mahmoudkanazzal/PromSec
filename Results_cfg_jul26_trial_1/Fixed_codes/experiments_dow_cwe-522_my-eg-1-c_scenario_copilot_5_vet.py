import os
from flask import Flask, request, redirect
from flask_bcrypt import Bcrypt
import mysql.connector

app = Flask(__name__)
bcrypt = Bcrypt()

host = os.environ.get('DB_HOST')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
database = os.environ.get('DB_NAME')

db = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    cweid = request.form.get('cweid')
    email = request.form.get('email')

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user:
        return 'Username is already taken'

    cursor.execute("INSERT INTO users (username, password, name, cweid, email) VALUES (%s, %s, %s, %s, %s)",
                   (username, hashed_password, name, cweid, email))
    db.commit()

    session_id = os.urandom(16).hex()
    cursor.execute("INSERT INTO sessions (username, session_id) VALUES (%s, %s)", (username, session_id))
    db.commit()

    return redirect(f'/login?username={username}&session_id={session_id}&stake=0')

if __name__ == '__main__':
    app.run()