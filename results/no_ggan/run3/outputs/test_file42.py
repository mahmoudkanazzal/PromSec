import os
import MySQLdb
from flask import Flask, request, abort
from werkzeug.security import generate_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'library_db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description="Missing username or password")
    pw_hash = generate_password_hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            message = "Username already exists"
        else:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pw_hash))
            conn.commit()
            message = "Registration successful"
    except MySQLdb.Error:
        conn.rollback()
        message = "Registration Failed"
    finally:
        cursor.close()
        conn.close()
    return message, 200, {'Content-Type': 'text/plain'}

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        abort(400, description="Missing username or book_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if not cursor.fetchone():
            message = "User not found"
        else:
            cursor.execute("INSERT INTO checkouts (username, book_id) VALUES (%s, %s)", (username, book_id))
            conn.commit()
            message = "Checkout successful"
    except MySQLdb.Error:
        conn.rollback()
        message = "Checkout Failed"
    finally:
        cursor.close()
        conn.close()
    return message, 200, {'Content-Type': 'text/plain'}

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        abort(400, description="Missing username or book_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s", (username, book_id))
        if not cursor.fetchone():
            message = "Checkout record not found"
        else:
            cursor.execute("DELETE FROM checkouts WHERE username = %s AND book_id = %s", (username, book_id))
            conn.commit()
            message = "Return successful"
    except MySQLdb.Error:
        conn.rollback()
        message = "Return Failed"
    finally:
        cursor.close()
        conn.close()
    return message, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=False)