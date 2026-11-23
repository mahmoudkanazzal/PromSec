from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL
        )''')
init_db()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if not title or not author or not genre:
        return jsonify({"error": "Missing required fields"}), 400
    with get_db_connection() as conn:
        conn.execute('INSERT INTO books (title, author, genre) VALUES (?, ?, ?)', (title, author, genre))
        conn.commit()
    return jsonify({"message": "Book added successfully"}), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f"%{keyword}%"
    with get_db_connection() as conn:
        cur = conn.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ?', (pattern, pattern))
        rows = cur.fetchall()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if not title or not author or not genre:
        return jsonify({"error": "Missing required fields"}), 400
    with get_db_connection() as conn:
        conn.execute('UPDATE books SET title = ?, author = ?, genre = ? WHERE id = ?', (title, author, genre, book_id))
        conn.commit()
    return jsonify({"message": "Book updated successfully"}), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()
    return jsonify({"message": "Book deleted successfully"}), 200

@app.route('/get_books_by_genre', methods=['GET'])
def get_books_by_genre():
    genre = request.args.get('genre', '')
    with get_db_connection() as conn:
        cur = conn.execute('SELECT * FROM books WHERE genre = ?', (genre,))
        rows = cur.fetchall()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=False)