import os
import sqlite3
from flask import Flask, request, jsonify

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', '')

@app.route('/add_book', methods=['POST'])
def add_book():
    if not request.is_json:
        return jsonify(error='Invalid JSON'), 400
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if not title or not author or not genre:
        return jsonify(error='Missing or empty fields'), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO books (title, author, genre) VALUES (?, ?, ?)',
                (title, author, genre)
            )
            conn.commit()
        return jsonify(message='Book added successfully'), 201
    except sqlite3.Error as e:
        return jsonify(error=str(e)), 500

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM books WHERE title LIKE ? OR author LIKE ?',
                (pattern, pattern)
            ).fetchall()
        result = [dict(row) for row in rows]
        return jsonify(result), 200
    except sqlite3.Error as e:
        return jsonify(error=str(e)), 500

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    if not request.is_json:
        return jsonify(error='Invalid JSON'), 400
    data = request.get_json()
    fields = {}
    for key in ('title', 'author', 'genre'):
        if key in data and data[key]:
            fields[key] = data[key]
    if not fields:
        return jsonify(error='No updatable fields provided'), 400
    set_clause = ', '.join([f'{k} = ?' for k in fields])
    params = list(fields.values()) + [book_id]
    try:
        with get_db_connection() as conn:
            cur = conn.execute(f'UPDATE books SET {set_clause} WHERE id = ?', params)
            conn.commit()
            if cur.rowcount == 0:
                return jsonify(error='Book not found'), 404
        return jsonify(message='Book updated successfully'), 200
    except sqlite3.Error as e:
        return jsonify(error=str(e)), 500

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        with get_db_connection() as conn:
            cur = conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
            conn.commit()
            if cur.rowcount == 0:
                return jsonify(error='Book not found'), 404
        return jsonify(message='Book deleted successfully'), 200
    except sqlite3.Error as e:
        return jsonify(error=str(e)), 500

@app.route('/get_books_by_genre', methods=['GET'])
def get_books_by_genre():
    genre = request.args.get('genre', '')
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT * FROM books WHERE genre = ?', (genre,)).fetchall()
        result = [dict(row) for row in rows]
        return jsonify(result), 200
    except sqlite3.Error as e:
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=False)