import os
import sqlite3
from flask import Flask, request, jsonify, abort

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                genre TEXT NOT NULL
            )
        ''')
        conn.commit()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
init_db()

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e.description)), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify(error='Resource not found'), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify(error='Internal server error'), 500

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        abort(400, description='JSON payload required')
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if not title or not author or not genre:
        abort(400, description='Fields title, author, and genre are required and cannot be empty')
    with get_db_connection() as conn:
        conn.execute('INSERT INTO books (title, author, genre) VALUES (?, ?, ?)', (title, author, genre))
        conn.commit()
    return jsonify(message='Book added successfully'), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM books WHERE title LIKE ? COLLATE NOCASE OR author LIKE ? COLLATE NOCASE', (pattern, pattern)).fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if not data:
        abort(400, description='JSON payload required')
    fields = {}
    for field in ('title', 'author', 'genre'):
        if field in data:
            value = data[field]
            if not value:
                abort(400, description=f'Field {field} cannot be empty')
            fields[field] = value
    if not fields:
        abort(400, description='No updatable fields provided')
    set_clause = ', '.join([f'{k} = ?' for k in fields.keys()])
    params = list(fields.values()) + [book_id]
    with get_db_connection() as conn:
        conn.execute(f'UPDATE books SET {set_clause} WHERE id = ?', params)
        conn.commit()
    return jsonify(message='Book updated successfully'), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()
    return jsonify(message='Book deleted successfully'), 200

@app.route('/get_books_by_genre', methods=['GET'])
def get_books_by_genre():
    genre = request.args.get('genre', '')
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM books WHERE genre = ?', (genre,)).fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=False)