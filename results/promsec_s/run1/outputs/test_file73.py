import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect, jsonify
from werkzeug.security import safe_str_cmp
from contextlib import closing

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')

def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.sha256(password.encode('utf-8') + salt).digest()
    return digest.hex() + salt.hex()

def verify_password(stored_hex, password):
    try:
        stored_hash = stored_hex[:64]
        stored_salt = stored_hex[64:]
        recomputed = hashlib.sha256(password.encode('utf-8') + bytes.fromhex(stored_salt)).digest().hex() + stored_salt
        return safe_str_cmp(recomputed, stored_hex)
    except Exception:
        return False

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/home')
    try:
        hashed = hash_password(password)
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
            conn.commit()
    except Exception as e:
        print(e)
    return redirect('/home')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Invalid credentials"
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT password FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
        if row and verify_password(row[0], password):
            return redirect('/dashboard')
    except Exception as e:
        print(e)
    return "Invalid credentials"

@app.route('/add_book', methods=['POST'])
def add_book():
    book_id = request.form.get('book_id')
    title = request.form.get('title')
    author = request.form.get('author')
    if not book_id or not title or not author:
        return "Failed to add book"
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("INSERT INTO books (book_id, title, author) VALUES (%s, %s, %s)", (book_id, title, author))
            conn.commit()
        return "Book successfully added"
    except Exception as e:
        print(e)
        return "Failed to add book"

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return "Checkout failed"
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if not cur.fetchone():
                    return "User not found"
                cur.execute("INSERT INTO checkouts (username, book_id) VALUES (%s, %s)", (username, book_id))
            conn.commit()
        return "Book successfully checked out"
    except Exception as e:
        print(e)
        return "Checkout failed"

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return "Return failed"
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s", (username, book_id))
                if not cur.fetchone():
                    return "Checkout record not found"
                cur.execute("DELETE FROM checkouts WHERE username = %s AND book_id = %s", (username, book_id))
            conn.commit()
        return "Book successfully returned"
    except Exception as e:
        print(e)
        return "Return failed"

@app.route('/view_books', methods=['GET'])
def view_books():
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT book_id, title, author FROM books")
                rows = cur.fetchall()
        books = [{'book_id': r[0], 'title': r[1], 'author': r[2]} for r in rows]
        return jsonify(books)
    except Exception as e:
        print(e)
        return "Failed to retrieve books"

if __name__ == '__main__':
    app.run(debug=False)