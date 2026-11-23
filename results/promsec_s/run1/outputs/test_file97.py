from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if title is None or author is None or genre is None:
        return jsonify({"error": "Missing required fields"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO books (title, author, genre) VALUES (?, ?, ?)', (title, author, genre))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Book added successfully"}), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f"%{keyword}%"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ?', (pattern, pattern))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if title is None or author is None or genre is None:
        return jsonify({"error": "Missing required fields"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE books SET title = ?, author = ?, genre = ? WHERE id = ?', (title, author, genre, book_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Book updated successfully"}), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Book deleted successfully"}), 200

@app.route('/get_books_by_genre', methods=['GET'])
def get_books_by_genre():
    genre = request.args.get('genre', '')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM books WHERE genre = ?', (genre,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=False)