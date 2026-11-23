from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    try:
        conn.enable_load_extension(False)
    except AttributeError:
        pass
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    if not title or not author:
        return jsonify(error='Missing title or author'), 400
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
        conn.commit()
    return jsonify(message='Book added'), 201

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')
    if not book_id or not book_id.isdigit():
        return jsonify(error='Invalid id'), 400
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM books WHERE id = ?', (int(book_id),))
        row = cur.fetchone()
    if row is None:
        return jsonify(error='Book not found'), 404
    return jsonify(dict(row)), 200

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json(silent=True) or {}
    try:
        book_id = int(data.get('book_id'))
        copies = int(data.get('copies'))
    except (TypeError, ValueError):
        return jsonify(error='Invalid book_id or copies'), 400
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('UPDATE books SET copies = copies + ? WHERE id = ?', (copies, book_id))
        if cur.rowcount == 0:
            return jsonify(error='Book not found'), 404
        conn.commit()
    return jsonify(message='Copies updated'), 200

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT title, author, copies FROM books ORDER BY title')
        rows = cur.fetchall()
    catalog = [dict(row) for row in rows]
    return jsonify(catalog), 200

if __name__ == '__main__':
    app.run(debug=False)