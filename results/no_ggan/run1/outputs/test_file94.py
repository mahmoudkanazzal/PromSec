from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data or 'title' not in data or 'author' not in data:
        return jsonify({'error': 'Missing title or author'}), 400
    title = data['title']
    author = data['author']
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO books (title, author, copies) VALUES (?, ?, 0)', (title, author))
        conn.commit()
        return jsonify({'message': 'Book added successfully'}), 201
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')
    if not book_id or not book_id.isdigit():
        return jsonify({'error': 'Invalid or missing book id'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM books WHERE id = ?', (int(book_id),))
        row = cur.fetchone()
        if row is None:
            return jsonify({'error': 'Book not found'}), 404
        return jsonify(row_to_dict(row)), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json()
    if not data or 'book_id' not in data or 'copies' not in data:
        return jsonify({'error': 'Missing book_id or copies'}), 400
    try:
        book_id = int(data['book_id'])
        copies = int(data['copies'])
    except (ValueError, TypeError):
        return jsonify({'error': 'book_id and copies must be integers'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE books SET copies = copies + ? WHERE id = ?', (copies, book_id))
        if cur.rowcount == 0:
            return jsonify({'error': 'Book not found'}), 404
        conn.commit()
        return jsonify({'message': 'Copies updated successfully'}), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT title, author, copies FROM books ORDER BY title')
        rows = cur.fetchall()
        books = [row_to_dict(row) for row in rows]
        return jsonify(books), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    conn = get_db_connection()
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT NOT NULL, copies INTEGER NOT NULL DEFAULT 0)')
        conn.commit()
    finally:
        conn.close()
    app.run(debug=False)