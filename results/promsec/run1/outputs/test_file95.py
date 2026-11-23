import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                author TEXT,
                year INTEGER
            )
        ''')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not isinstance(title, str) or not isinstance(author, str) or not isinstance(year, int):
        return jsonify({'error': 'Invalid data types'}), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO books (title, author, year) VALUES (?, ?, ?)',
                (title, author, year)
            )
        return jsonify({'message': 'Book added successfully'}), 201
    except Exception:
        return jsonify({'error': 'Database error'}), 500

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    try:
        with get_db_connection() as conn:
            if keyword:
                rows = conn.execute(
                    '''
                    SELECT * FROM books
                    WHERE LOWER(title) LIKE LOWER(?)
                    OR LOWER(author) LIKE LOWER(?)
                    ''',
                    (pattern, pattern)
                ).fetchall()
            else:
                rows = conn.execute('SELECT * FROM books').fetchall()
        result = [dict(row) for row in rows]
        return jsonify(result), 200
    except Exception:
        return jsonify({'error': 'Database error'}), 500

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title') if 'title' in data else None
    author = data.get('author') if 'author' in data else None
    year = data.get('year') if 'year' in data else None
    if 'year' in data and not isinstance(year, int):
        return jsonify({'error': 'Year must be integer'}), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                '''
                UPDATE books
                SET title = ?, author = ?, year = ?
                WHERE id = ?
                ''',
                (title, author, year, book_id)
            )
        return jsonify({'message': 'Book updated successfully'}), 200
    except Exception:
        return jsonify({'error': 'Database error'}), 500

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
        return jsonify({'message': 'Book deleted successfully'}), 200
    except Exception:
        return jsonify({'error': 'Database error'}), 500

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year_param = request.args.get('year')
    try:
        with get_db_connection() as conn:
            if year_param is not None and year_param != '':
                try:
                    year = int(year_param)
                except ValueError:
                    return jsonify({'error': 'Year must be integer'}), 400
                rows = conn.execute('SELECT * FROM books WHERE year = ?', (year,)).fetchall()
            else:
                rows = conn.execute('SELECT * FROM books').fetchall()
        result = [dict(row) for row in rows]
        return jsonify(result), 200
    except Exception:
        return jsonify({'error': 'Database error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False)