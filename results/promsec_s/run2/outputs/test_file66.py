from __future__ import annotations
import os, hashlib, logging
from flask import Flask, request, redirect
import MySQLdb
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST','localhost'),
        user=os.getenv('DB_USER','root'),
        passwd=os.getenv('DB_PASS',''),
        db=os.getenv('DB_NAME','test')
    )
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username','')
    password = request.form.get('password','')
    pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM User WHERE username = %s", (username,))
        if cursor.fetchone():
            return redirect('./register')
        cursor.execute("INSERT INTO User (username, password) VALUES (%s, %s)", (username, pwd_hash))
        conn.commit()
        return redirect('./login')
    except Exception as e:
        logging.error("Database error: %s", e)
        return "Internal Server Error", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
if __name__ == '__main__':
    app.run()