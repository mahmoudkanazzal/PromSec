from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dicts(rows):
    return [dict(row) for row in rows]

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

init_db()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        abort(400, description='Invalid or missing JSON payload')
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if not title or not author or not genre:
        abort(400, description='Missing required fields: title, author, genre')
    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO books (title, author, genre) VALUES (?, ?, ?)',
            (title, author, genre)
        )
        conn.commit()
    return jsonify(message='Book added successfully'), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    with get_db_connection() as conn:
        cursor = conn.execute(
            'SELECT * FROM books WHERE title LIKE ? OR author LIKE ?',
            (pattern, pattern)
        )
        rows = cursor.fetchall()
    return jsonify(rows_to_dicts(rows)), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if not data:
        abort(400, description='Invalid or missing JSON payload')
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if not title or not author or not genre:
        abort(400, description='Missing required fields: title, author, genre')
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE books SET title = ?, author = ?, genre = ? WHERE id = ?',
            (title, author, genre, book_id)
        )
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
    genre = request.args.get('genre')
    if not genre:
        abort(400, description='Missing required query parameter: genre')
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM books WHERE genre = ?', (genre,))
        rows = cursor.fetchall()
    return jsonify(rows_to_dicts(rows)), 200

if __name__ == '__main__':
    app.run(debug=False)