import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'library.db')

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Book added successfully'})

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id=?", (book_id,))
    book = cursor.fetchone()
    conn.close()

    return jsonify({'book': book})

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json()
    book_id = data.get('id')
    copies = data.get('copies')

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE books SET copies = copies + ? WHERE id=?", (copies, book_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Copies updated successfully'})

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    catalog = cursor.fetchall()
    conn.close()

    return jsonify({'catalog': catalog})

if __name__ == '__main__':
    app.run()