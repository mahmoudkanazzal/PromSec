import os
import logging
from flask import Flask, request
import MySQLdb
import bcrypt
from contextlib import closing

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

MAX_USERNAME_LEN = 150
MAX_PASSWORD_LEN = 150

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', autocommit=False)

def validate_username(username):
    return isinstance(username, str) and 1 <= len(username) <= MAX_USERNAME_LEN

def validate_password(password):
    return isinstance(password, str) and 1 <= len(password) <= MAX_PASSWORD_LEN

def validate_book_id(book_id):
    try:
        return int(book_id) > 0
    except Exception:
        return False

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not (validate_username(username) and validate_password(password)):
        return "Registration Failed"
    try:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                if cur.fetchone():
                    return "Username already exists"
                cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
                conn.commit()
        return "You have successfully registered"
    except MySQLdb.Error as e:
        logging.error(e)
        return "Registration Failed"
    except Exception as e:
        logging.error(e)
        return "Registration Failed"

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username', '')
    book_id = request.form.get('book_id', '')
    if not (validate_username(username) and validate_book_id(book_id)):
        return "Checkout Failed"
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT id FROM users WHERE username=%s", (username,))
                row = cur.fetchone()
                if not row:
                    return "User not found"
                user_id = row[0]
                cur.execute("INSERT INTO checkouts (user_id, book_id) VALUES (%s, %s)", (user_id, int(book_id)))
                conn.commit()
        return "Book successfully checked out"
    except MySQLdb.Error as e:
        logging.error(e)
        return "Checkout Failed"
    except Exception as e:
        logging.error(e)
        return "Checkout Failed"

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username', '')
    book_id = request.form.get('book_id', '')
    if not (validate_username(username) and validate_book_id(book_id)):
        return "Return Failed"
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT id FROM users WHERE username=%s", (username,))
                row = cur.fetchone()
                if not row:
                    return "Checkout record not found"
                user_id = row[0]
                cur.execute("SELECT id FROM checkouts WHERE user_id=%s AND book_id=%s", (user_id, int(book_id)))
                checkout_row = cur.fetchone()
                if not checkout_row:
                    return "Checkout record not found"
                cur.execute("DELETE FROM checkouts WHERE id=%s", (checkout_row[0],))
                conn.commit()
        return "Book successfully returned"
    except MySQLdb.Error as e:
        logging.error(e)
        return "Return Failed"
    except Exception as e:
        logging.error(e)
        return "Return Failed"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)