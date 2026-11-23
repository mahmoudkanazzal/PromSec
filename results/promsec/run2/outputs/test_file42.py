import os
from contextlib import closing
import MySQLdb
import bcrypt
from flask import Flask, request

app = Flask(__name__)

def db_params():
    return {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'passwd': os.getenv('DB_PASSWORD'),
        'db': os.getenv('DB_NAME')
    }

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return "Registration Failed"
    try:
        with closing(MySQLdb.connect(**db_params())) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                if cur.fetchone():
                    return "Username already exists"
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
                conn.commit()
                return "You have successfully registered"
    except Exception:
        return "Registration Failed"

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    book_id = data.get('book_id')
    if not username or not book_id:
        return "Checkout Failed"
    try:
        with closing(MySQLdb.connect(**db_params())) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                if not cur.fetchone():
                    return "User not found"
                cur.execute("INSERT INTO checkouts (username, book_id) VALUES (%s, %s)", (username, book_id))
                conn.commit()
                return "Book successfully checked out"
    except Exception:
        return "Checkout Failed"

@app.route('/return', methods=['POST'])
def return_book():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    book_id = data.get('book_id')
    if not username or not book_id:
        return "Return Failed"
    try:
        with closing(MySQLdb.connect(**db_params())) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT 1 FROM checkouts WHERE username=%s AND book_id=%s", (username, book_id))
                if not cur.fetchone():
                    return "Checkout record not found"
                cur.execute("DELETE FROM checkouts WHERE username=%s AND book_id=%s", (username, book_id))
                conn.commit()
                return "Book successfully returned"
    except Exception:
        return "Return Failed"

if __name__ == '__main__':
    app.run(debug=False)