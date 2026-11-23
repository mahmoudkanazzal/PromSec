import os
import sqlite3
import subprocess
import shlex
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
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE NOT NULL
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_books():
    db = get_db()
    cur = db.execute('SELECT * FROM books')
    rows = cur.fetchall()
    return [dict(row) for row in rows]

def add_book(title, author, isbn):
    db = get_db()
    db.execute('INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)',
               (title, author, isbn))
    db.commit()

def delete_book(book_id):
    db = get_db()
    db.execute('DELETE FROM books WHERE id = ?', (book_id,))
    db.commit()

def run_user_command(cmd):
    # Execute commands without invoking a shell to prevent injection
    args = shlex.split(cmd)
    subprocess.run(args, capture_output=True, text=True)

@app.route('/books', methods=['GET'])
def list_books():
    return jsonify(query_books())

@app.route('/books', methods=['POST'])
def create_book():
    data = request.get_json(force=True)
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        add_book(title, author, isbn)
    except sqlite3.IntegrityError:
        return jsonify({'error': 'ISBN must be unique'}), 400
    return jsonify({'status': 'book added'}), 201

@app.route('/books/<int:book_id>', methods=['DELETE'])
def remove_book(book_id):
    delete_book(book_id)
    return jsonify({'status': 'book deleted'})

@app.route('/search')
def search():
    q = request.args.get('q', '')
    cmd = f'grep -i "{q}" books.txt'
    run_user_command(cmd)
    return jsonify({'command': cmd, 'message': 'search executed'})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)