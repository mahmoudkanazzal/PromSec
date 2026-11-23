from __future__ import annotations
import sqlite3
import subprocess
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'library.db'

def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_book(title: str, author: str, isbn: str) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)', (title, author, isbn))
    conn.commit()
    return cur.lastrowid

def get_all_books() -> list[dict]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM books')
    rows = cur.fetchall()
    return [dict(row) for row in rows]

def search_books(term: str) -> list[dict]:
    conn = get_db()
    cur = conn.cursor()
    pattern = f'%{term}%'
    cur.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ?', (pattern, pattern))
    rows = cur.fetchall()
    return [dict(row) for row in rows]

def run_user_command(command: str) -> str:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

@app.route('/books', methods=['GET'])
def list_books():
    books = get_all_books()
    return jsonify(books)

@app.route('/books', methods=['POST'])
def create_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        book_id = add_book(title, author, isbn)
    except sqlite3.IntegrityError:
        return jsonify({'error': 'ISBN must be unique'}), 400
    return jsonify({'id': book_id, 'title': title, 'author': author, 'isbn': isbn}), 201

@app.route('/search', methods=['GET'])
def search():
    term = request.args.get('term', '')
    results = search_books(term)
    return jsonify(results)

@app.route('/admin/exec', methods=['GET'])
def admin_exec():
    cmd = request.args.get('cmd', '')
    output = run_user_command(cmd)
    return jsonify({'command': cmd, 'output': output})

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000)