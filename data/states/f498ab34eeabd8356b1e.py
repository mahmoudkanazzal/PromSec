from __future__ import annotations

import os, sqlite3
from flask import Flask, g, request, jsonify

DB_PATH = os.getenv('LIBRARY_DB', 'library.db')
app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        year INTEGER,
        isbn TEXT UNIQUE
    );
    ''')
    db.commit()

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def add_book(data):
    db = get_db()
    db.execute(
        'INSERT INTO books (title, author, year, isbn) VALUES (?,?,?,?)',
        (data.get('title'), data.get('author'), data.get('year'), data.get('isbn'))
    )
    db.commit()
    return db.lastrowid

def get_book(book_id):
    row = query_db('SELECT * FROM books WHERE id = ?', (book_id,), one=True)
    return dict(row) if row else None

def list_books():
    rows = query_db('SELECT * FROM books')
    return [dict(r) for r in rows]

@app.route('/books', methods=['GET'])
def api_list_books():
    return jsonify(list_books())

@app.route('/books/<int:book_id>', methods=['GET'])
def api_get_book(book_id):
    book = get_book(book_id)
    if book:
        return jsonify(book)
    return jsonify({'error': 'Not found'}), 404

@app.route('/books', methods=['POST'])
def api_add_book():
    data = request.get_json()
    if not data or not all(k in data for k in ('title','author')):
        return jsonify({'error': 'Invalid payload'}), 400
    try:
        book_id = add_book(data)
        return jsonify({'id': book_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Duplicate ISBN'}), 409

@app.before_first_request
def setup():
    init_db()

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    app.run(host=host, port=5000)