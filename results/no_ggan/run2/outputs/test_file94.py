from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
app.debug = False

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    return {k: row[k] for k in row.keys()}

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    if not title or not author:
        return jsonify({'error': 'Missing title or author'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
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
        return jsonify({'error': 'Invalid id'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        row = cur.fetchone()
        if row is None:
            return jsonify({'error': 'Book not found'}), 404
        return jsonify(dict_from_row(row)), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json(silent=True) or {}
    book_id = data.get('book_id')
    copies = data.get('copies')
    if book_id is None or copies is None:
        return jsonify({'error': 'Missing book_id or copies'}), 400
    try:
        book_id_int = int(book_id)
        copies_int = int(copies)
    except (ValueError, TypeError):
        return jsonify({'error': 'book_id and copies must be integers'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE books SET copies = copies + ? WHERE id = ?', (copies_int, book_id_int))
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
        books = [dict_from_row(row) for row in rows]
        return jsonify(books), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()