from flask import Flask, request, redirect
import re, hashlib, os
import mysql.connector
from werkzeug.security import generate_password_hash

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/')
    hashed_password = generate_password_hash(password)
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '69.195.55.111'),
            user=os.getenv('DB_USER', 'ec2-user'),
            password=os.getenv('DB_PASSWORD', 'ufo12345'),
            database=os.getenv('DB_NAME', 'CWE')
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO User (Username, Password, Email) VALUES (%s, %s, %s)",
            (username, hashed_password, username)
        )
        conn.commit()
    except Exception:
        return redirect('/')
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()