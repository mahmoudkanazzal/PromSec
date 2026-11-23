import os
import logging
import sqlite3
from flask import Flask, request, jsonify
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        try:
            conn.execute('''CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )''')
            conn.commit()
        except sqlite3.Error as e:
            logging.error('Database initialization error: %s', e)

init_db()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not isinstance(title, str) or not title.strip():
        return jsonify({'error': 'Title must be a non‑empty string'}), 400
    if not isinstance(author, str) or not author.strip():
        return jsonify({'error': 'Author must be a non‑empty string'}), 400
    if not isinstance(year, int):
        return jsonify({'error': 'Year must be an integer'}), 400
    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO books (title, author, year) VALUES (?, ?, ?)', (title.strip(), author.strip(), year))
            conn.commit()
        return jsonify({'message': 'Book added successfully'}), 201
    except sqlite3.Error as e:
        logging.error('Database error on add_book: %s', e)
        return jsonify({'error': 'Internal server error'}), 500
    except Exception:
        logging.exception('Unexpected error on add_book')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword')
    try:
        with get_db_connection() as conn:
            if keyword:
                pattern = f'%{keyword}%'
                cur = conn.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ?', (pattern, pattern))
            else:
                cur = conn.execute('SELECT * FROM books')
            rows = [dict(row) for row in cur.fetchall()]
        return jsonify(rows), 200
    except sqlite3.Error as e:
        logging.error('Database error on search_books: %s', e)
        return jsonify({'error': 'Internal server error'}), 500
    except Exception:
        logging.exception('Unexpected error on search_books')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    fields = {}
    if 'title' in data:
        title = data['title']
        if not isinstance(title, str) or not title.strip():
            return jsonify({'error': 'Title must be a non‑empty string'}), 400
        fields['title'] = title.strip()
    if 'author' in data:
        author = data['author']
        if not isinstance(author, str) or not author.strip():
            return jsonify({'error': 'Author must be a non‑empty string'}), 400
        fields['author'] = author.strip()
    if 'year' in data:
        year = data['year']
        if not isinstance(year, int):
            return jsonify({'error': 'Year must be an integer'}), 400
        fields['year'] = year
    if not fields:
        return jsonify({'error': 'No valid fields provided'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT 1 FROM books WHERE id = ?', (book_id,))
            if not cur.fetchone():
                return jsonify({'error': 'Book not found'}), 404
            set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
            values = list(fields.values())
            values.append(book_id)
            conn.execute(f'UPDATE books SET {set_clause} WHERE id = ?', values)
            conn.commit()
        return jsonify({'message': 'Book updated successfully'}), 200
    except sqlite3.Error as e:
        logging.error('Database error on update_book: %s', e)
        return jsonify({'error': 'Internal server error'}), 500
    except Exception:
        logging.exception('Unexpected error on update_book')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        with get_db_connection() as conn:
            cur = conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
            conn.commit()
            if cur.rowcount == 0:
                return jsonify({'error': 'Book not found'}), 404
        return jsonify({'message': 'Book deleted successfully'}), 200
    except sqlite3.Error as e:
        logging.error('Database error on delete_book: %s', e)
        return jsonify({'error': 'Internal server error'}), 500
    except Exception:
        logging.exception('Unexpected error on delete_book')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year_param = request.args.get('year')
    if year_param is None:
        return jsonify({'error': 'Year parameter is required'}), 400
    try:
        year = int(year_param)
    except ValueError:
        return jsonify({'error': 'Year must be an integer'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT * FROM books WHERE year = ?', (year,))
            rows = [dict(row) for row in cur.fetchall()]
        return jsonify(rows), 200
    except sqlite3.Error as e:
        logging.error('Database error on get_books_by_year: %s', e)
        return jsonify({'error': 'Internal server error'}), 500
    except Exception:
        logging.exception('Unexpected error on get_books_by_year')
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)