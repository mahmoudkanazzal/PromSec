from __future__ import annotations
import os
import sqlite3
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'library.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                author TEXT,
                year INTEGER,
                isbn TEXT
            )
        ''')
        conn.commit()
        conn.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def add_book_to_db(title: str, author: str, year: int, isbn: str) -> int:
    db = get_db()
    query = "INSERT INTO books (title, author, year, isbn) VALUES (?, ?, ?, ?)"
    cur = db.cursor()
    cur.execute(query, (title, author, year, isbn))
    db.commit()
    return cur.lastrowid

def search_books_in_db(title: str | None, author: str | None, year: str | None) -> list[dict]:
    db = get_db()
    base = "SELECT * FROM books WHERE 1=1"
    params: list = []
    if title:
        base += " AND title LIKE ?"
        params.append(f"%{title}%")
    if author:
        base += " AND author LIKE ?"
        params.append(f"%{author}%")
    if year:
        base += " AND year = ?"
        params.append(year)
    cur = db.cursor()
    cur.execute(base, params)
    rows = cur.fetchall()
    return [dict(row) for row in rows]

@app.route('/add', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title', '')
    author = data.get('author', '')
    year = int(data.get('year', 0))
    isbn = data.get('isbn', '')
    book_id = add_book_to_db(title, author, year, isbn)
    return jsonify({'status': 'ok', 'id': book_id})

@app.route('/search', methods=['GET'])
def search_books():
    title = request.args.get('title')
    author = request.args.get('author')
    year = request.args.get('year')
    results = search_books_in_db(title, author, year)
    return jsonify(results)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)