import os
import hashlib
import hmac
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_pass, db_name]):
        raise RuntimeError('Database configuration environment variables missing')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        sql = "SELECT id, username, password, accesslevel FROM user WHERE username = %s"
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        if not row:
            return "User does not exist"
        stored_hash = row[2]
        supplied_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if not hmac.compare_digest(supplied_hash, stored_hash):
            return "Incorrect Password"
        return redirect('/user')
    except MySQLdb.Error:
        return "Internal Server Error", 500
    except Exception:
        return "Internal Server Error", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(debug=False)