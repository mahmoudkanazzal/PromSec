from __future__ import print_function
import hashlib
import time
import sqlite3
import secrets
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DB_PATH = 'library.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT UNIQUE,
                       password TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS books (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       title TEXT,
                       author TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS sessions (
                       token TEXT PRIMARY KEY,
                       username TEXT,
                       created REAL)''')
    db.commit()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def generate_token(username):
    token = secrets.token_urlsafe(32)
    db = get_db()
    db.execute('INSERT INTO sessions (token, username, created) VALUES (?,?,?)',
               (token, username, time.time()))
    db.commit()
    return token

def verify_token(token):
    db = get_db()
    row = db.execute('SELECT username FROM sessions WHERE token=?', (token,)).fetchone()
    return row['username'] if row else None

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'missing fields'}), 400
    pw_hash = hash_password(password)
    db = get_db()
    try:
        db.execute('INSERT INTO users (username, password) VALUES (?,?)',
                   (username, pw_hash))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'user exists'}), 400
    return jsonify({'status': 'registered'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'missing fields'}), 400
    pw_hash = hash_password(password)
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE username=? AND password=?',
                     (username, pw_hash)).fetchone()
    if row is None:
        return jsonify({'error': 'invalid credentials'}), 401
    token = generate_token(username)
    return jsonify({'token': token})

def token_required(f):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'token required'}), 401
        username = verify_token(parts[1])
        if not username:
            return jsonify({'error': 'invalid token'}), 401
        g.current_user = username
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/books', methods=['GET'])
def list_books():
    db = get_db()
    rows = db.execute('SELECT id, title, author FROM books').fetchall()
    books = [{'id': r['id'], 'title': r['title'], 'author': r['author']} for r in rows]
    return jsonify(books)

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    db = get_db()
    row = db.execute('SELECT id, title, author FROM books WHERE id=?', (book_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'id': row['id'], 'title': row['title'], 'author': row['author']})

@app.route('/books', methods=['POST'])
@token_required
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    if not title or not author:
        return jsonify({'error': 'missing fields'}), 400
    db = get_db()
    cur = db.execute('INSERT INTO books (title, author) VALUES (?,?)', (title, author))
    db.commit()
    return jsonify({'id': cur.lastrowid, 'title': title, 'author': author}), 201

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=False)