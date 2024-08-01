import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_FILE = 'books.db'

if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT NOT NULL,
                 author TEXT NOT NULL,
                 genre TEXT NOT NULL)''')
    conn.commit()
    conn.close()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO books (title, author, genre) VALUES (?, ?, ?)",
              (data['title'], data['author'], data['genre']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book added successfully'})

@app.route('/search_books_by_genre', methods=['GET'])
def search_books_by_genre():
    genre = request.args.get('genre')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE genre=?", (genre,))
    books = c.fetchall()
    conn.close()
    return jsonify({'books': books})

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE books SET title=?, author=?, genre=? WHERE id=?",
              (data['title'], data['author'], data['genre'], book_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book updated successfully'})

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book deleted successfully'})

@app.route('/get_books_by_genre/<string:genre>', methods=['GET'])
def get_books_by_genre(genre):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE genre=?", (genre,))
    books = c.fetchall()
    conn.close()
    return jsonify({'books': books})

if __name__ == '__main__':
    app.run(debug=True)