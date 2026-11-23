from __future__ import annotations
import os
import hashlib
import pymysql
from flask import Flask, request, redirect, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')


def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', ''),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


def valid_field(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not (valid_field(username) and valid_field(password)):
        return redirect('/home')
    try:
        salt = os.urandom(16)
        pwd_hash = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=64)
        stored = (salt + pwd_hash).hex()
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, stored)
                )
        finally:
            conn.close()
    except Exception as e:
        print(e)
    return redirect('/home')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not (valid_field(username) and valid_field(password)):
        return 'Invalid credentials'
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT password FROM users WHERE username = %s",
                    (username,)
                )
                row = cur.fetchone()
        finally:
            conn.close()
        if not row:
            return 'Invalid credentials'
        stored_hex = row['password']
        stored_bytes = bytes.fromhex(stored_hex)
        salt = stored_bytes[:16]
        stored_hash = stored_bytes[16:]
        pwd_hash = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=64)
        if pwd_hash == stored_hash:
            return redirect('/dashboard')
        else:
            return 'Invalid credentials'
    except Exception as e:
        print(e)
        return 'Invalid credentials'


@app.route('/add_book', methods=['POST'])
def add_book():
    book_id = request.form.get('book_id', '')
    title = request.form.get('title', '')
    author = request.form.get('author', '')
    if not (valid_field(book_id) and valid_field(title) and valid_field(author)):
        return 'Failed to add book'
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO books (book_id, title, author) VALUES (%s, %s, %s)",
                    (book_id, title, author)
                )
        finally:
            conn.close()
        return 'Book successfully added'
    except Exception as e:
        print(e)
        return 'Failed to add book'


@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username', '')
    book_id = request.form.get('book_id', '')
    if not (valid_field(username) and valid_field(book_id)):
        return 'Checkout failed'
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM users WHERE username = %s",
                    (username,)
                )
                if not cur.fetchone():
                    return 'User not found'
                cur.execute(
                    "INSERT INTO checkouts (username, book_id) VALUES (%s, %s)",
                    (username, book_id)
                )
        finally:
            conn.close()
        return 'Book successfully checked out'
    except Exception as e:
        print(e)
        return 'Checkout failed'


@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username', '')
    book_id = request.form.get('book_id', '')
    if not (valid_field(username) and valid_field(book_id)):
        return 'Return failed'
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s",
                    (username, book_id)
                )
                if not cur.fetchone():
                    return 'Checkout record not found'
                cur.execute(
                    "DELETE FROM checkouts WHERE username = %s AND book_id = %s",
                    (username, book_id)
                )
        finally:
            conn.close()
        return 'Book successfully returned'
    except Exception as e:
        print(e)
        return 'Return failed'


@app.route('/view_books', methods=['GET'])
def view_books():
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT book_id, title, author FROM books")
                rows = cur.fetchall()
        finally:
            conn.close()
        return jsonify(rows)
    except Exception as e:
        print(e)
        return 'Failed to retrieve books'


if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port, debug=False)