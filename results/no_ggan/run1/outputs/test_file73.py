import os
import logging
import hashlib
import hmac
import json
from typing import Any, List, Dict
from flask import Flask, request, redirect, url_for, jsonify, Response
import MySQLdb

# Configuration
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'library')

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_db_connection() -> MySQLdb.connections.Connection:
    """Create a new MySQL database connection using environment variables."""
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True
    )

def rows_to_dicts(cursor: MySQLdb.cursors.Cursor) -> List[Dict[str, Any]]:
    """Convert cursor result set to list of dictionaries using column names."""
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def hash_password(password: str) -> str:
    """Hash a password with a random 16‑byte salt using PBKDF2‑HMAC‑SHA256."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000, dklen=32)
    return (salt + dk).hex()

def verify_password(stored_hex: str, password: str) -> bool:
    """Verify a password against the stored hex representation of salt+hash."""
    stored_bytes = bytes.fromhex(stored_hex)
    salt = stored_bytes[:16]
    stored_hash = stored_bytes[16:]
    new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000, dklen=32)
    return hmac.compare_digest(stored_hash, new_hash)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

@app.route('/register', methods=['POST'])
def register() -> Response:
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    hashed = hash_password(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed)
        )
        conn.commit()
        return redirect(url_for('home'))
    except Exception:
        logger.exception("Error during registration")
        return 'Registration failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login() -> Response:
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password FROM users WHERE username = %s",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return 'Invalid credentials', 401
        stored_hash = row[0]
        if verify_password(stored_hash, password):
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials', 401
    except Exception:
        logger.exception("Error during login")
        return 'Login failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/add_book', methods=['POST'])
def add_book() -> Response:
    book_id = request.form.get('book_id')
    title = request.form.get('title')
    author = request.form.get('author')
    if not book_id or not title or not author:
        return 'Missing book_id, title, or author', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books (book_id, title, author) VALUES (%s, %s, %s)",
            (book_id, title, author)
        )
        conn.commit()
        return 'Book successfully added', 201
    except Exception:
        logger.exception("Error adding book")
        return 'Failed to add book', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/checkout', methods=['POST'])
def checkout() -> Response:
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return 'Missing username or book_id', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM users WHERE username = %s",
            (username,)
        )
        if not cursor.fetchone():
            return 'User not found', 404
        cursor.execute(
            "INSERT INTO checkouts (username, book_id) VALUES (%s, %s)",
            (username, book_id)
        )
        conn.commit()
        return 'Book successfully checked out', 200
    except Exception:
        logger.exception("Error during checkout")
        return 'Checkout failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/return', methods=['POST'])
def return_book() -> Response:
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return 'Missing username or book_id', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s",
            (username, book_id)
        )
        if not cursor.fetchone():
            return 'Checkout record not found', 404
        cursor.execute(
            "DELETE FROM checkouts WHERE username = %s AND book_id = %s",
            (username, book_id)
        )
        conn.commit()
        return 'Book successfully returned', 200
    except Exception:
        logger.exception("Error during return")
        return 'Return failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_books', methods=['GET'])
def view_books() -> Response:
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        books = rows_to_dicts(cursor)
        return jsonify(books), 200
    except Exception:
        logger.exception("Error retrieving books")
        return 'Failed to retrieve books', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/home', methods=['GET'])
def home() -> Response:
    return 'Welcome to the home page', 200

@app.route('/dashboard', methods=['GET'])
def dashboard() -> Response:
    return 'Welcome to your dashboard', 200

if __name__ == '__main__':
    app.run(debug=False)